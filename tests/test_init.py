"""Non-destructive tests: every test keeps its own fixture under .scratch."""
from pathlib import Path
import sys
import unittest
from uuid import uuid4

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
import init

class InitializationTests(unittest.TestCase):
    def setUp(self):
        base=ROOT/'tests/.scratch'
        base.mkdir(parents=True,exist_ok=True)
        self.target=base/('project-'+uuid4().hex)

    def test_new_project_has_isolated_project_state(self):
        init.setup(self.target,'Fresh Project','new',False)
        self.assertTrue((self.target/'AGENTS.md').exists())
        self.assertTrue((self.target/'.codex/agents/qa.toml').exists())
        self.assertIn('Fresh Project',(self.target/'tracking/state.json').read_text(encoding='utf-8'))
        self.assertFalse((self.target/'.git').exists())

    def test_default_both_installs_claude_and_codex(self):
        init.setup(self.target, 'Both', 'new', False)
        self.assertTrue((self.target/'CLAUDE.md').exists())
        self.assertTrue((self.target/'.claude/agents/qa.md').exists())
        self.assertTrue((self.target/'.codex/agents/qa.toml').exists())
        self.assertTrue((self.target/'tracking/state.json').exists())
        self.assertIn('@AGENTS.md',(self.target/'CLAUDE.md').read_text(encoding='utf-8'))

    def test_claude_only_excludes_codex_config(self):
        init.setup(self.target, 'Claude', 'new', False, 'claude')
        self.assertTrue((self.target/'CLAUDE.md').exists())
        self.assertTrue((self.target/'.claude/settings.json').exists())
        self.assertFalse((self.target/'.codex').exists())
        self.assertFalse((self.target/'START-CODEX.md').exists())
        self.assertTrue((self.target/'tracking/state.json').exists())

    def test_codex_only_excludes_claude_config(self):
        init.setup(self.target, 'Codex', 'new', False, 'codex')
        self.assertFalse((self.target/'CLAUDE.md').exists())
        self.assertFalse((self.target/'.claude').exists())
        self.assertTrue((self.target/'.codex/agents/reviewer.toml').exists())
        self.assertTrue((self.target/'tracking/state.json').exists())

    def test_claude_settings_is_parseable_and_no_bypass(self):
        import json
        init.setup(self.target, 'Claude', 'new', False, 'claude')
        cfg=json.loads((self.target/'.claude/settings.json').read_text(encoding='utf-8'))
        self.assertEqual(cfg['permissions']['defaultMode'],'default')
        self.assertEqual(cfg['permissions']['disableBypassPermissionsMode'],'disable')

    def test_existing_file_is_never_overwritten(self):
        self.target.mkdir()
        (self.target/'AGENTS.md').write_text('my personal AGENTS',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Refusing to overwrite'):
            init.setup(self.target,'Existing','install',False)
        self.assertEqual((self.target/'AGENTS.md').read_text(encoding='utf-8'),'my personal AGENTS')
        self.assertFalse((self.target/'tracking/state.json').exists())

    def test_reject_install_inside_source(self):
        with self.assertRaisesRegex(ValueError,'separate'):
            init.verify_destination(str(ROOT/'nested-project'))

    def test_existing_junction_or_symlink_is_refused_when_available(self):
        self.target.mkdir()
        actual=self.target/'actual';actual.mkdir()
        link=self.target/'alias'
        try:
            link.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation unavailable')
        with self.assertRaisesRegex(ValueError,'symlink/junction'):
            init.verify_destination(str(link/'somewhere'))

if __name__=='__main__':unittest.main()
