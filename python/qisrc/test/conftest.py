# export all fixtures form qisys tests:
from qisys.test.conftest import *

import qisrc.git
import qisrc.worktree
import qisrc.manifest
import qisys.script

class TestGitWorkTree(qisrc.worktree.GitWorkTree):
    """ A subclass of qisrc.worktree.WorkTree that
    can create git projects

    """
    def __init__(self, worktree=None):
        if not worktree:
            worktree = TestWorkTree()
        super(TestGitWorkTree, self).__init__(worktree)

    @property
    def tmpdir(self):
        # pylint: disable-msg=E1101
        return py.path.local(self.root)

    def create_git_project(self, src, branch="master"):
        """ Create a new git project """
        to_make = os.path.join(self.root, src)
        qisys.sh.mkdir(to_make, recursive=True)
        test_git = TestGit(to_make)
        test_git.initialize(branch=branch)

        new_project = super(TestGitWorkTree, self).add_git_project(src)
        return new_project

class TestGitServer(object):
    """ Represent a set of git urls

    everything is done relative to the <root> parameter

<root>
  |__ srv
       # here be bare repos
       foo.git
       bar.git
  |_ gerrit
      # here be clones of bare repos,
      # used to test qisrc review for instance
      foo.git
      bar.git
  |__ src
        # temporary clones use to populate the
        # bare repos in srv/ and gerrit/
        foo
        bar
 |__ work
        # where we will create worktrees and make our testing
        # (used by qisrc_action fixture for instanc

    Two remotes are created by default: "origin" and "gerrit"

    """
    def __init__(self, root):
        self.root = root
        self.srv = root.mkdir("srv")
        self.src = root.mkdir("src")
        self.gerrit = root.mkdir("gerrit")
        self.work = root.mkdir("work")

        # Manifest itself can not be handled as a normal repo:
        self._create_repo("manifest.git")
        self.push_file("manifest.git", "manifest.xml", "<manifest />")
        manifest_xml = root.join("src", "manifest", "manifest.xml")
        self.manifest = qisrc.manifest.Manifest(manifest_xml.strpath)
        self.manifest.add_remote("origin", self.srv.strpath)
        self.manifest.add_remote("gerrit",  self.gerrit.strpath, review=True)
        self.manifest_url = self.srv.join("manifest.git").strpath

    def create_repo(self, project, src=None, review=False):
        """ Create a new repo and add it to the manifest """
        self._create_repo(project, src=src, review=False)
        if review:
            self._create_repo(project, src=src, review=True)
            self.manifest.add_repo(project, src, ["origin", "gerrit"])
        else:
            self.manifest.add_repo(project, src, ["origin"])
        repo = self.manifest.get_repo(project)

        manifest_repo = self.root.join("src", "manifest")
        git = qisrc.git.Git(manifest_repo.strpath)
        git.commit("--all", "--message", "add %s" % src)
        git.push("origin", "master:master")
        return repo

    def _create_repo(self, project, src=None, review=False):
        """ Helper for self.create_repo """
        if not src:
            src = project.replace(".git", "")

        if review:
            repo_srv = self.gerrit.mkdir(project)
        else:
            repo_srv = self.srv.mkdir(project)
        git = qisrc.git.Git(repo_srv.strpath)
        git.init("--bare")

        repo_src = self.src.ensure(src, dir=True)
        git = TestGit(repo_src.strpath)
        git.initialize()
        if review:
            git.set_remote("gerrit", repo_srv.strpath)
            git.push("gerrit", "master:master")
        else:
            git.set_remote("origin", repo_srv.strpath)
            git.push("origin", "master:master")


    def get_repo(self, project):
        """ Get a repo from the manifest """
        return self.manifest.get_repo(project)

    def move_repo(self, project, new_src):
        """ Change a repo location """
        repo = self.manifest.get_repo(project)
        old_src = repo.src
        repo.src = new_src
        self.manifest.dump()
        self.push_manifest("%s: moved %s -> %s" % (project, old_src, new_src))
        self.manifest.load()

    def push_manifest(self, message):
        """ Push new manifest.xml version """
        manifest_repo = self.root.join("src", "manifest")
        git = qisrc.git.Git(manifest_repo.strpath)
        git.commit("--all", "--message", message)
        git.call("show", "HEAD")
        git.push("origin", "master:master")

    def remove_repo(self, project):
        """ Remove a repo from the manifest """
        self.manifest.remove_repo(project)
        self.push_manifest("removed %s" % project)

    def create_group(self, name, projects):
        """ Add a group to the manifest """
        for project in projects:
            self.create_repo(project)
        self.manifest.configure_group(name, projects)
        self.push_manifest("add group %s" % name)

    def use_review(self, project):
        """ Switch a project to gerrit for code review """
        self._create_repo(project, review=True)
        repo = self.manifest.get_repo(project)
        repo.remote_names.append("gerrit")
        self.manifest.dump()
        self.push_manifest("%s: now under code review" % project)
        self.manifest.load()

    def push_file(self, project, filename, contents,
                  branch="master", fast_forward=True):
        """ Push a new file with the given contents to the given project
        It is assumed that the project has beed created

        """
        src = project.replace(".git", "")
        repo_src = self.src.join(src)
        git = qisrc.git.Git(repo_src.strpath)
        if not fast_forward:
            git.reset("--hard", "HEAD~1")
        to_write = repo_src.join(filename)
        if to_write.check(file=True):
            message = "Update %s" % filename
        else:
            message = "Add %s" % filename
        repo_src.join(filename).write(contents)
        git.checkout("--force", "-B", branch)
        git.add(filename)
        git.commit("--message", message)
        if fast_forward:
            git.push("origin", "%s:%s" % (branch, branch))
        else:
            git.push("origin", "--force", "%s:%s" % (branch, branch))


class TestGit(qisrc.git.Git):
    """ the Git class with a few other helpfull methods """
    def __init__(self, repo=None):
        if repo is None:
            repo = os.getcwd()
        super(TestGit, self).__init__(repo)

    @property
    def root(self):
        # pylint: disable-msg=E1101
        return py.path.local(self.repo)

    def initialize(self, branch="master"):
        """ Make sure there is at least one commit and one branch """
        rc, out = self.call("show", raises=False)
        if rc == 0:
            return
        self.init()
        self.checkout("-b", branch)
        self.root.join(".gitignore").write("")
        self.add(".gitignore")
        self.commit("--message", "initial commit")

    def read_file(self, path):
        """ Read the contents of a file """
        return self.root.join(path).read()

    def commit_file(self, path, contents, message=None):
        """ Commit a file. Path will be created if it does not exits """
        file_path = self.root.join(path)
        file_path.write(contents)
        if not message:
            message = "Create/update %s" % path
        self.add(path)
        self.commit("--message", message)

class FakeGit(qisrc.git.Git):
    """ To be used as a mock object for testing

    """
    # Pseudo persistent config
    repo_configs = dict()

    def __init__(self, repo):
        self.repo = repo
        if not self.repo in FakeGit.repo_configs:
            FakeGit.repo_configs[repo] = dict()
        self.calls = list()
        self.calls_index = dict()
        self.results = dict()

    def get_config(self, name):
        return FakeGit.repo_configs[self.repo].get(name)

    def set_config(self, name, value):
        FakeGit.repo_configs[self.repo][name] = value

    def add_result(self, cmd, retcode, out):
        """ Add an expected result for the given command

        """
        if cmd in self.results:
            self.results[cmd].append((retcode, out))
        else:
            self.results[cmd] = [(retcode, out)]

    def get_result(self, cmd):
        """ Look for the expected result

        """
        if not cmd in self.results:
            raise Exception("Unexpected call to %s" % cmd)
        if not cmd in self.calls_index:
            self.calls_index[cmd] = 0
        index = self.calls_index[cmd]
        res_list = self.results[cmd]
        if index >= len(res_list):
            mess = "%s was called %s times " % (cmd, index+1)
            mess += "but only %s results were configured" % (len(res_list))
            raise Exception(mess)
        res = self.results[cmd][index]
        self.calls_index[cmd] += 1
        return res

    def check(self):
        """ Check that everything that was configured has been called """
        for (k, v) in self.results.iteritems():
            call_index = self.calls_index.get(k)
            if call_index is None:
                mess = "%s was added as result but never called" % k
                raise Exception(mess)
            if call_index != len(v):
                mess = "%s was configured to be called %s times " % (k, len(v))
                mess += "but was only called %s times" % (call_index)
                raise Exception(mess)

    def called(self, cmd):
        """ Return True if the command was called """
        for (call_args, _) in self.calls:
            if call_args[0] == cmd:
                return True
        return False

    def _call(self, *args, **kwargs):
        """ Look for the return of the command in the list.
        If not found, assume it succeeds.

        """
        self.calls.append((args, kwargs))
        (retcode, out) = self.get_result(args[0])
        raises = kwargs.get("raises")
        if raises is False:
            return (retcode, out)
        else:
            if retcode != 0:
                raise Exception("%s failed" % " ".join(args))


# pylint: disable-msg=E1101
@pytest.fixture
def git_worktree(cd_to_tmpdir):
    return TestGitWorkTree()

# pylint: disable-msg=E1101
@pytest.fixture
def test_git(request):
    return TestGit

# pylint: disable-msg=E1101
@pytest.fixture
def git_server(tmpdir):
    # pylint: disable-msg=E1101
    git_srv = TestGitServer(tmpdir.mkdir("git"))
    return git_srv

# pylint: disable-msg=E1101
@pytest.fixture
def mock_git(request):
    return FakeGit("repo")

# pylint: disable-msg=E1101
@pytest.fixture
def qisrc_action(cd_to_tmpdir):
    return QiSrcAction()

class QiSrcAction(TestAction):
    def __init__(self):
        super(QiSrcAction, self).__init__("qisrc.actions")
        self.root = self.worktree.root
        self.git_worktree = TestGitWorkTree(worktree=self.worktree)

    def create_git_project(self, src, branch="master"):
        return self.git_worktree.create_git_project(src, branch=branch)

    def reload_worktree(self):
        self.worktree = TestWorkTree(root=self.root)
        self.git_worktree = TestGitWorkTree(worktree=self.worktree)

    @property
    def tmpdir(self):
        return self.git_worktree.tmpdir
