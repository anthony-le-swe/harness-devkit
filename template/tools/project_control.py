#!/usr/bin/env python3
"""Local-first project tracker with independent QA/review gate and safe checkpoints.

No external packages. The CLI is a workflow validator, NOT a security sandbox or
cryptographically authenticated approval system.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import html
import json
import os
from pathlib import Path
import shutil
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / 'tracking/state.json'
EVENTS = ROOT / 'tracking/events.jsonl'
HANDOFF = ROOT / 'tracking/handoff.json'
HANDOFF_MD = ROOT / 'docs/SESSION_HANDOFF.md'
STATUS_MD = ROOT / 'docs/PROJECT_STATUS.md'
DASHBOARD = ROOT / 'dashboard/index.html'
STATUSES = {'todo', 'in_progress', 'in_review', 'blocked', 'done'}


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def inside(path: Path):
    """Refuse paths escaping project or traversing symlinks/junctions."""
    resolved = path.resolve(strict=False)
    if resolved != ROOT and ROOT not in resolved.parents:
        raise ValueError(f'Outside project: {path}')
    current = path
    while current != ROOT:
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise ValueError(f'Symlink/junction path rejected: {current}')
        current = current.parent
    return path


def read_json(path: Path):
    inside(path)
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def write_file(path: Path, data: str, preserve=True):
    inside(path)
    inside(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    if preserve and path.exists():
        backup = ROOT / 'tracking/backups' / (timestamp().replace(':','-') + '-' + uuid4().hex + '-' + path.name + '.bak')
        inside(backup)
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    temporary = path.with_name('.' + path.name + '.' + uuid4().hex + '.pending')
    inside(temporary)
    with temporary.open('x', encoding='utf-8', newline='\n') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    # Atomic normal replacement of a tracker artifact; old bytes preserved in backups.
    os.replace(temporary, path)


def save_json(path, value, preserve=True):
    write_file(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n', preserve)


def event(kind, subject, actor, message, **extra):
    inside(EVENTS)
    record = {'at': timestamp(), 'kind': kind, 'subject': subject, 'actor': actor, 'message': message, **extra}
    with EVENTS.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return record


def state_read():
    s = read_json(STATE)
    if not isinstance(s, dict) or not isinstance(s.get('tasks'), list) or not isinstance(s.get('decisions'), list):
        raise ValueError('Invalid tracking/state.json schema')
    return s


def find_task(s, ident):
    for task in s['tasks']:
        if task['id'] == ident:
            return task
    raise ValueError(f'Unknown task: {ident}')


def require_role(actor, owner):
    if not actor.strip() or actor.casefold() == owner.casefold():
        raise ValueError('Independent actor must be named and different from implementer')


def task_add(a):
    s = state_read()
    if any(t['id'] == a.id for t in s['tasks']):
        raise ValueError(f'Duplicate task ID: {a.id}')
    s['tasks'].append({'id': a.id, 'title': a.title, 'owner': a.owner, 'acceptance': a.acceptance,
        'priority': a.priority, 'status': 'todo', 'approved': False, 'revision': 0,
        'qa': None, 'review': None, 'evidence': '', 'blocked_reason': ''})
    save_json(STATE, s)
    event('task-created', a.id, 'orchestrator', a.title)


def task_approve(a):
    s = state_read(); t = find_task(s, a.id)
    if not a.by.strip():
        raise ValueError('Approver required')
    t['approved'] = True
    t['approved_by'] = a.by
    save_json(STATE,s)
    event('scope-approved', a.id, a.by, 'Approval recorded (actor is self-reported)')


def task_start(a):
    s = state_read(); t = find_task(s,a.id)
    if not t['approved']:
        raise ValueError('Task scope not approved')
    if t['status'] == 'done':
        raise ValueError('Cannot reopen Done without a separate approved change task')
    t['status'] = 'in_progress'; t['blocked_reason'] = ''
    save_json(STATE,s)
    event('task-started',a.id,t['owner'],a.note)


def task_submit(a):
    s = state_read(); t = find_task(s,a.id)
    if not t['approved'] or t['status'] != 'in_progress':
        raise ValueError('Only approved in-progress task can be submitted')
    t['revision'] += 1
    t['status'] = 'in_review'; t['qa'] = None; t['review'] = None
    t['evidence'] = a.evidence
    save_json(STATE,s)
    event('submitted',a.id,t['owner'],a.evidence,revision=t['revision'])


def task_qa(a):
    s=state_read();t=find_task(s,a.id)
    if t['status'] != 'in_review' or not t['revision']:
        raise ValueError('Task must be submitted for current revision')
    require_role(a.actor,t['owner'])
    t['qa']={'status':a.result,'actor':a.actor,'evidence':a.evidence,'revision':t['revision'],'at':timestamp()}
    t['review']=None
    save_json(STATE,s)
    event('qa',a.id,a.actor,a.evidence,result=a.result,revision=t['revision'])


def task_review(a):
    s=state_read();t=find_task(s,a.id)
    if t['status'] != 'in_review' or not t['qa'] or t['qa']['status'] != 'pass' or t['qa']['revision'] != t['revision']:
        raise ValueError('Current revision must have QA PASS before reviewer approval')
    require_role(a.actor,t['owner'])
    if a.actor.casefold() == t['qa']['actor'].casefold():
        raise ValueError('Reviewer and QA must be different actors')
    t['review']={'status':a.result,'actor':a.actor,'evidence':a.evidence,'revision':t['revision'],'at':timestamp()}
    save_json(STATE,s)
    event('review',a.id,a.actor,a.evidence,result=a.result,revision=t['revision'])


def gate(t):
    qa=t.get('qa') or {}; rv=t.get('review') or {}
    return (bool(t.get('approved')) and bool(t.get('acceptance')) and bool(t.get('evidence'))
        and t.get('revision',0)>0 and qa.get('status')=='pass' and rv.get('status')=='approved'
        and bool(qa.get('evidence')) and bool(rv.get('evidence'))
        and qa.get('revision') == t.get('revision') == rv.get('revision')
        and len({str(t['owner']).casefold(),str(qa.get('actor','')).casefold(),str(rv.get('actor','')).casefold()}) == 3)


def task_done(a):
    s=state_read();t=find_task(s,a.id)
    if t['status'] != 'in_review' or not gate(t):
        raise ValueError('Gate denied: current revision requires independent QA PASS + Reviewer APPROVED and evidence')
    t['status']='done';t['completed_at']=timestamp()
    save_json(STATE,s)
    event('task-done',a.id,'orchestrator','QA and Reviewer approved; evidence persisted',revision=t['revision'])


def task_block(a):
    s=state_read();t=find_task(s,a.id)
    if t['status']=='done':
        raise ValueError('Cannot block completed task')
    t['status']='blocked';t['blocked_reason']=a.reason
    save_json(STATE,s)
    event('blocked',a.id,'orchestrator',a.reason)


def decision_propose(a):
    s=state_read()
    if any(d['id']==a.id for d in s['decisions']):
        raise ValueError('Duplicate ADR ID')
    d={'id':a.id,'title':a.title,'status':'proposed','proposal':a.proposal,'alternatives':a.alternatives,
       'context':a.context,'approved_by':'','created_at':timestamp()}
    s['decisions'].append(d)
    save_json(STATE,s)
    doc=ROOT/'docs/decisions'/(a.id+'.md')
    write_file(doc, f'# {a.id}: {a.title}\n\nStatus: Proposed\n\n## Context\n{a.context}\n\n## Proposal\n{a.proposal}\n\n## Alternatives\n{a.alternatives}\n',False)
    event('adr-proposed',a.id,'architect',a.title)


def decision_approve(a):
    s=state_read();d=next((d for d in s['decisions'] if d['id']==a.id),None)
    if not d: raise ValueError('Unknown ADR')
    if not a.by.strip(): raise ValueError('Named human owner required')
    d['status']='approved';d['approved_by']=a.by;d['approved_at']=timestamp()
    save_json(STATE,s)
    event('adr-approved',a.id,a.by,'Human approval recorded (self-reported)')


def checkpoint(a):
    old={'schema':1,'task':a.task,'done':a.done,'next_action':a.next_action,
         'files':[x.strip() for x in a.files.split(',') if x.strip()], 'tests':a.tests,'at':timestamp()}
    # Explicit checkpoint is the only operation allowed to replace existing handoff.
    save_json(HANDOFF,old)
    write_file(HANDOFF_MD,'# Session handoff\n\n'+ '\n'.join([
        f'- Saved: {old["at"]}', f'- Task: {a.task or "none"}', f'- Done: {a.done}',
        f'- Tests: {a.tests}', f'- Next: {a.next_action}',
        f'- Modified files: {", ".join(old["files"]) or "none"}'])+'\n')
    event('checkpoint',a.task or 'project','orchestrator',a.next_action)
    print(json.dumps(old,indent=2,ensure_ascii=False))


def init_handoff(_):
    # Must check existence BEFORE inspecting contents, including malformed, empty, {}.
    if HANDOFF.exists() or HANDOFF_MD.exists():
        raise ValueError('Handoff already exists (even if empty/malformed); preserved. Use explicit checkpoint to replace.')
    s=state_read()
    initial={'schema':1,'task':'','done':'Initialized project tracker','next_action':'Review the approved backlog',
             'files':[],'tests':'Not run','at':timestamp()}
    save_json(HANDOFF,initial,False)
    write_file(HANDOFF_MD,f'# Session handoff\n\n- Project: {s.get("name", "")}\n- Next: Review the approved backlog\n',False)
    event('handoff-init','project','orchestrator','Initialized missing handoff')


def resume(_):
    s=state_read()
    print(json.dumps({'project':s.get('name'), 'handoff': read_json(HANDOFF) if HANDOFF.exists() else None,
          'unfinished':[{'id':t['id'],'title':t['title'],'status':t['status'], 'approved':t['approved']} for t in s['tasks'] if t['status']!='done']},indent=2,ensure_ascii=False))


def validate(_):
    s=state_read();ids=set()
    for t in s['tasks']:
        if t['id'] in ids: raise ValueError('Duplicate task IDs')
        ids.add(t['id'])
        if t['status'] not in STATUSES: raise ValueError('Invalid task status')
        if t['status']=='done' and not gate(t): raise ValueError(f'Invalid Done gate: {t["id"]}')
    if HANDOFF.exists():
        h=read_json(HANDOFF)
        if not isinstance(h,dict) or not h.get('next_action'):
            raise ValueError('Invalid or incomplete handoff; do NOT init-handoff to replace it')
    if EVENTS.exists():
        for number,line in enumerate(EVENTS.read_text(encoding='utf-8').splitlines(),1):
            try: json.loads(line)
            except json.JSONDecodeError: raise ValueError(f'Invalid JSONL line {number}')
    print(f'VALID: {len(s["tasks"])} tasks, {len(s["decisions"])} ADRs; done gates checked')


def dashboard(_):
    s=state_read();h=read_json(HANDOFF) if HANDOFF.exists() else {}
    tasks=s['tasks']; counts={status:sum(t['status']==status for t in tasks) for status in sorted(STATUSES)}
    pct=round(100*counts['done']/len(tasks)) if tasks else 0
    data={'name':s.get('name','Project'),'goal':s.get('goal',''),'tasks':tasks,'decisions':s['decisions'],
          'counts':counts,'progress':pct,'handoff':h}
    safe=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    page="""<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Codex Project Control</title><style>
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif;background:#0c1322;color:#e9eef7}*{box-sizing:border-box}body{max-width:1240px;margin:auto;padding:28px 22px}h1{font-size:30px;letter-spacing:-.9px;margin:0}p{color:#94a3b8}.muted{color:#94a3b8;font-size:13px}.stats,.board{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.panel,.card{background:#141f33;border:1px solid #2a3b56;border-radius:14px;padding:16px}.stat{font-size:30px;font-weight:750}.bar{background:#304056;height:12px;border-radius:99px;overflow:hidden;margin:14px 0}.bar>div{height:100%;background:#2dd4bf}.column{min-width:0;background:#101a2c;border:1px solid #263851;border-radius:14px;padding:12px}.column h3{font-size:15px}.card{margin:8px 0;padding:12px;word-break:break-word}.card strong{font-size:14px}.chip{display:inline-block;font-size:11px;border:1px solid #4a5d79;border-radius:99px;padding:3px 7px;margin:5px 5px 0 0}section{margin-top:28px}button,select{background:#1d2b46;color:#e7ecf6;border:1px solid #425372;border-radius:9px;padding:9px;cursor:pointer}code{color:#b4d6ff}ul{padding-left:18px}li{margin-bottom:6px}@media(max-width:650px){body{padding:18px 12px}.board{grid-template-columns:1fr 1fr}}@media(max-width:390px){.board{grid-template-columns:1fr}} </style></head><body>
<header><div class="muted">LOCAL PROJECT CONTROL CENTER · SNAPSHOT</div><h1 id="name"></h1><p id="goal"></p></header><div class="stats" id="stats"></div><div class="bar"><div id="progress"></div></div><div class="muted" id="progressText"></div>
<section><h2>Task board</h2><label>Filter <select id="filter"><option value="all">All tasks</option><option value="todo">Todo</option><option value="in_progress">In progress</option><option value="in_review">In review</option><option value="blocked">Blocked</option><option value="done">Done</option></select></label><div class="board" id="board"></div></section>
<section class="panel"><h2>Checkpoint / Resume</h2><div id="handoff"></div></section><section class="panel"><h2>Decisions / ADR</h2><div id="decisions"></div></section>
<p class="muted">Generated snapshot from tracking/state.json + tracking/handoff.json. Rebuild with <code>py -3 tools/project_control.py dashboard</code> and refresh browser. Recorded QA/Review is not identity-verified.</p>
<script>const d=__DATA__;const E=(tag,text,cls)=>{let el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el};document.querySelector('#name').textContent=d.name;document.querySelector('#goal').textContent=d.goal||'No goal defined';document.querySelector('#progress').style.width=d.progress+'%';document.querySelector('#progressText').textContent=d.progress+'% complete · '+d.tasks.length+' tasks';let stats=document.querySelector('#stats');for(let [k,v] of Object.entries(d.counts)){let p=E('div','', 'panel');p.append(E('div',String(v),'stat'),E('div',k.replaceAll('_',' '),'muted'));stats.append(p)}
const labels=['todo','in_progress','in_review','blocked','done'];const board=document.querySelector('#board');function draw(){board.replaceChildren();for(let status of labels){let c=E('div','', 'column');c.append(E('h3',status.replaceAll('_',' ').toUpperCase()));for(let t of d.tasks.filter(x=>x.status===status&&(filter.value==='all'||filter.value===status))){let item=E('div','', 'card');item.append(E('strong',t.id+' · '+t.title),E('div','Owner: '+t.owner,'muted'),E('div','Revision '+t.revision+' · '+(t.approved?'approved':'needs scope approval'),'muted'),E('span','QA: '+(t.qa?.status||'pending'),'chip'),E('span','Review: '+(t.review?.status||'pending'),'chip'));c.append(item)}board.append(c)}}const filter=document.querySelector('#filter');filter.addEventListener('change',draw);draw();let h=d.handoff||{};document.querySelector('#handoff').append(E('div','Task: '+(h.task||'none')),E('div','Done: '+(h.done||'—')),E('div','Next: '+(h.next_action||'—')));let decisions=document.querySelector('#decisions');if(!d.decisions.length)decisions.append(E('p','No ADRs yet'));for(let a of d.decisions)decisions.append(E('div',a.id+' · '+a.title+' — '+a.status,'card'));</script></body></html>""".replace('__DATA__',safe)
    write_file(DASHBOARD,page)
    digest=f'# {s.get("name","Project")} — Project status\n\nProgress: {pct}% ({counts["done"]}/{len(tasks)})\n\n'
    for t in tasks:
        digest+=f'- {t["id"]} [{t["status"]}] {t["title"]} | QA: {(t.get("qa") or {}).get("status", "pending")} | Review: {(t.get("review") or {}).get("status", "pending")}\n'
    digest+='\nNext: '+str(h.get('next_action','Not recorded'))+'\n'
    write_file(STATUS_MD,digest)
    print(f'Dashboard regenerated: {DASHBOARD} ({pct}% complete)')


def event_add(a):
    event(a.kind,a.subject,a.actor,a.message)


def main():
    p=argparse.ArgumentParser(description='Codex AI team project control')
    subs=p.add_subparsers(dest='cmd',required=True)
    def cmd(name,fn):
        x=subs.add_parser(name);x.set_defaults(func=fn);return x
    def fields(x,*pairs):
        for name,req in pairs:x.add_argument('--'+name.replace('_','-'),dest=name,required=req)
    x=cmd('task-add',task_add);fields(x,('id',True),('title',True),('owner',True),('acceptance',True));x.add_argument('--priority',type=int,default=3)
    x=cmd('task-approve',task_approve);fields(x,('id',True),('by',True))
    x=cmd('task-start',task_start);fields(x,('id',True),('note',True))
    x=cmd('task-submit',task_submit);fields(x,('id',True),('evidence',True))
    x=cmd('task-qa',task_qa);fields(x,('id',True),('actor',True),('evidence',True));x.add_argument('--result',choices=['pass','fail','blocked'],required=True)
    x=cmd('task-review',task_review);fields(x,('id',True),('actor',True),('evidence',True));x.add_argument('--result',choices=['approved','changes_requested','blocked'],required=True)
    x=cmd('task-done',task_done);fields(x,('id',True))
    x=cmd('task-block',task_block);fields(x,('id',True),('reason',True))
    x=cmd('decision-propose',decision_propose);fields(x,('id',True),('title',True),('proposal',True),('alternatives',True),('context',True))
    x=cmd('decision-approve',decision_approve);fields(x,('id',True),('by',True))
    x=cmd('checkpoint',checkpoint);fields(x,('next_action',True),('done',True));x.add_argument('--task',default='');x.add_argument('--files',default='');x.add_argument('--tests',default='Not run')
    cmd('init-handoff',init_handoff);cmd('resume',resume);cmd('dashboard',dashboard);cmd('validate',validate)
    x=cmd('event-add',event_add);fields(x,('kind',True),('subject',True),('actor',True),('message',True))
    a=p.parse_args()
    try:
        a.func(a)
        return 0
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as err:
        print(f'ERROR: {err}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
