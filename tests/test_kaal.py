"""Kaal test suite — stdlib unittest, zero deps. Run: python3 -m unittest discover tests"""
import os, sys, unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestRouter(unittest.TestCase):
    def test_endpoints_20(self):
        from kaal.models.router import list_endpoints, select_endpoint
        self.assertGreaterEqual(len(list_endpoints()), 20)
        self.assertEqual(select_endpoint()["name"], "omniroute/auto")

    def test_no_keys_fallback(self):
        from kaal.models.router import try_llm
        self.assertEqual(try_llm("hi"), ("rule-based", ""))


class TestPermissions(unittest.TestCase):
    def test_deny_blocks(self):
        from kaal.agent import run_task
        r = run_task("delete x", ask_cb=lambda q: False)
        self.assertEqual(r["status"], "denied")


class TestFiles(unittest.TestCase):
    def test_write_edit_undo(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "t.txt")
        f.write_file(p, "hello")
        self.assertIn("hello", f.read_file(p))
        r = f.edit_file(p, "hello", "world", lambda q: True)
        self.assertIn("Edit ho gayi", r)
        self.assertIn("world", f.read_file(p))
        u = f.undo_last(p)
        self.assertIn("Undo ho gaya", u)
        self.assertIn("hello", f.read_file(p))

    def test_outline_chunk(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp2")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "a.py")
        f.write_file(p, "def foo():\n pass\n" * 50)
        self.assertIn("foo", f.outline(p))
        self.assertIn("[lines 0-5/", f.read_file(p, 2000, 0, 5))


class TestSandbox(unittest.TestCase):
    def test_code_ok_and_block(self):
        from kaal.skills.code import run_python
        self.assertEqual(run_python("print(2+2)"), "4")
        self.assertIn("Block", run_python("import os; os.system('x')"))

    def test_shell_allowlist(self):
        from kaal.skills.shell import run
        self.assertEqual(run("echo hi", lambda q: True), "hi")
        self.assertIn("Block", run("rm -rf /", lambda q: True))
        self.assertIn("cancel", run("ls", lambda q: False))


class TestBrain(unittest.TestCase):
    def test_mock_loop(self):
        from kaal.models import brain
        script = [
            ("m", '{"thinking": "list", "tool": {"name": "file_list", "args": {"path": "."}}}'),
            ("m", '{"thinking": "done", "done": "ok mock"}'),
        ]
        brain.try_chat = lambda msgs: script.pop(0)
        todos, summary, ep = brain.run("t", ask_cb=lambda q: True)
        self.assertEqual(summary, "ok mock")
        self.assertEqual(ep, "m")


class TestOrchestrator(unittest.TestCase):
    def test_classify(self):
        from kaal.agents.orchestrator import decompose
        jobs = decompose("code fix karo aur github check karo")
        agents = {j["agent"] for j in jobs}
        self.assertIn("coder", agents)
        self.assertIn("github_specialist", agents)


class TestPower(unittest.TestCase):
    def test_checkpoint_rewind(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp3")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "c.txt")
        f.write_file(p, "v1")
        f.checkpoint("t")
        f.edit_file(p, "v1", "v2", lambda q: True)
        self.assertIn("v2", f.read_file(p))
        self.assertIn("Rewind", f.rewind())
        self.assertIn("v1", f.read_file(p))

    def test_plan_and_recipes(self):
        from kaal.planner import draft, write, read
        steps = draft("code fix karo aur test chalao")
        self.assertGreaterEqual(len(steps), 1)
        write("t", steps)
        self.assertIn("Plan", read())
        try:
            os.remove("PLAN.md")
        except OSError:
            pass
        from kaal.recipes import list_all, get
        self.assertIn("morning-review", list_all())
        self.assertGreaterEqual(len(get("morning-review")), 1)

    def test_local_skills(self):
        from kaal.skills import rules
        os.makedirs(".kaal/skills", exist_ok=True)
        with open(".kaal/skills/t.md", "w") as fh:
            fh.write("keywords: zaptest\n\nZap rule")
        self.addCleanup(lambda: __import__("shutil").rmtree(".kaal", ignore_errors=True))
        self.assertIn("Zap rule", rules.match("please zaptest now"))

    def test_changelog(self):
        from kaal.skills.git import changelog
        self.assertIn("Features", changelog(5))

    def test_export(self):
        from kaal.memory.store import save, export_md
        save("export test", "export summary")
        p = os.path.abspath("memory/.test-export.md")
        self.addCleanup(lambda: os.path.exists(p) and os.remove(p))
        self.assertIn("Export ho gaya", export_md(p))


if __name__ == "__main__":
    unittest.main()
