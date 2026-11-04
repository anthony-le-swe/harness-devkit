"""Independent gate and checkpoint semantics tested using retained fixtures."""
from pathlib import Path
import json
import subprocess
import sys
import unittest
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import init

class TrackerTests(unittest.TestCase):
    def setUp(self):
        base=ROOT/'tests/.scratch';base.mkdir(parents=True,exist_ok=True)
        self.dest=base/('tracker-'+uuid4().hex)
        init.setup(self.dest,'QA Test','new',False)
        self.tracker=self.dest/'tools/project_control.py'

    def cmd(self,*args,ok=True):
        result=subprocess.run([sys.executable,'-B',str(self.tracker),*args],cwd=self.dest,capture_output=True,text=True)
        if ok and result.returncode:
            self.fail(f'Unexpected CLI error: {result.stderr}')
        if not ok:self.assertNotEqual(result.returncode,0)
        return result

    def add(self):
        self.cmd('task-add','--id','T-1','--title','Feature','--owner','backend_dev','--acceptance','API passes tests')
        self.cmd('task-approve','--id','T-1','--by','Human owner')
        self.cmd('task-start','--id','T-1','--note','started')
        self.cmd('task-submit','--id','T-1','--evidence','diff ready')

    def test_gate_requires_independent_qa_and_reviewer(self):
        self.add()
        self.cmd('task-done','--id','T-1',ok=False)
        self.cmd('task-qa','--id','T-1','--actor','backend_dev','--result','pass','--evidence','fake',ok=False)
        self.cmd('task-qa','--id','T-1','--actor','qa','--result','pass','--evidence','12 tests passed')
        self.cmd('task-done','--id','T-1',ok=False)
        self.cmd('task-review','--id','T-1','--actor','qa','--result','approved','--evidence','review',ok=False)
        self.cmd('task-review','--id','T-1','--actor','reviewer','--result','approved','--evidence','diff reviewed')
        self.cmd('task-done','--id','T-1')
        self.cmd('validate')
        state=json.loads((self.dest/'tracking/state.json').read_text())
        self.assertEqual(state['tasks'][0]['status'],'done')

    def test_new_revision_invalidates_both_gates(self):
        self.add()
        self.cmd('task-qa','--id','T-1','--actor','qa','--result','pass','--evidence','tests')
        self.cmd('task-review','--id','T-1','--actor','reviewer','--result','approved','--evidence','diff')
        self.cmd('task-start','--id','T-1','--note','after changes')
        self.cmd('task-submit','--id','T-1','--evidence','new diff')
        self.cmd('task-done','--id','T-1',ok=False)
        self.cmd('validate')
        t=json.loads((self.dest/'tracking/state.json').read_text())['tasks'][0]
        self.assertEqual(t['revision'],2)
        self.assertIsNone(t['qa'])
        self.assertIsNone(t['review'])

    def test_handoff_init_preserves_partial_existing_data(self):
        h=self.dest/'tracking/handoff.json'
        md=self.dest/'docs/SESSION_HANDOFF.md'
        old_md=md.read_bytes();h.write_text('{}',encoding='utf-8')
        old_h=h.read_bytes();events=(self.dest/'tracking/events.jsonl').read_bytes()
        self.cmd('init-handoff',ok=False)
        self.assertEqual(h.read_bytes(),old_h)
        self.assertEqual(md.read_bytes(),old_md)
        self.assertEqual((self.dest/'tracking/events.jsonl').read_bytes(),events)
        self.cmd('checkpoint','--task','T-1','--done','checkpoint created','--next-action','continue')
        self.assertEqual(json.loads(h.read_text())['next_action'],'continue')
        self.cmd('resume')

    def test_dashboard_and_events(self):
        self.add();self.cmd('dashboard');self.cmd('validate')
        page=(self.dest/'dashboard/index.html').read_text(encoding='utf-8')
        self.assertIn('Task board',page)
        self.assertIn('T-1',page)
        self.assertIn('QA:',page)

if __name__=='__main__':unittest.main()
