from command_comparer import *

BASELINE_MSBUILD_EXE = Path(
    r'E:\projects\msbuild_2\artifacts\bin\bootstrap\net472\MSBuild\Current\Bin\MSBuild.exe')
CACHE_MSBUILD_EXE = Path(
    r'E:\projects\msbuild\artifacts\bin\bootstrap\net472\MSBuild\Current\Bin\MSBuild.exe')
CACHE_INITIALIZATION_LOGGER_DLL = Path(
    r"E:\projects\CloudBuild\private\Tools\MSBuildCacheInitializationLogger\src\objd\amd64\MSBuildCacheInitializationLogger.dll")
TEST_REPOS_ROOT = Path(r"E:\qb_repos")
CACHE = Path(r"E:\CloudBuildCache")
QUICKBUILD_INSTALLATION = Path(
    r"C:/Users/micodoba/AppData/Local/CloudBuild/quickbuild")

assert QUICKBUILD_INSTALLATION.is_dir()
QUICKBUILD_EXE = next(QUICKBUILD_INSTALLATION.glob(r"**\quickbuild.exe"), None)
assert QUICKBUILD_EXE is not None
assert QUICKBUILD_EXE.is_file()

CLEAN_REPOSITORY = ProcessCommand("git", "clean", "-xdf")

DELETE_QB_CACHE = PowershellCommand(
    f"if (Test-Path {str(CACHE)}) {{rm -recurse -force {str(CACHE)} ; Write-Output 'Deleted: {str(CACHE)}'}}" +
    f" else {{Write-Output 'Does not exist: {str(CACHE)}'}}")

MSBUILD_RESTORE = ProcessCommand(
    str(BASELINE_MSBUILD_EXE), "/t:restore", "/m", "dirs.proj")

MSBUILD_COMMON_ARGS = (
    "/graph", "/m", "/clp:'verbosity=minimal;summary'", "/restore:false", "dirs.proj")

MSBUILD_BASELINE_BUILD = ProcessCommand(
    str(BASELINE_MSBUILD_EXE), *MSBUILD_COMMON_ARGS)

MSBUILD_QB_FU2D_BUILD = ProcessCommand(str(CACHE_MSBUILD_EXE), *MSBUILD_COMMON_ARGS, "/p:BuildProjectReferences=false",
                                       f"/logger:CacheInitializationLogger,{CACHE_INITIALIZATION_LOGGER_DLL}")

MSBUILD_FU2D_BUILD = ProcessCommand(
    str(CACHE_MSBUILD_EXE), *MSBUILD_COMMON_ARGS, "/p:BuildProjectReferences=false")

QUICKBUILD_BUILD = ProcessCommand(
    str(QUICKBUILD_EXE), "-notest", "-msbuildrestore:false")

REPOS = [
    RepoSpec(
        "cloudbuild",
        r"private\BuildEngine\Enlistment.Library",  # 32 build nodes
        r"private\BuildEngine"  # 124 build nodes
    )
]

TEST_SUITES = [
    TestSuite(
        name="qb",
        tests=[
            Test(
                name="clean_remote_cache",
                repo_root_setup_command=Commands(
                    DELETE_QB_CACHE, CLEAN_REPOSITORY),
                setup_command=MSBUILD_RESTORE,
                test_command=QUICKBUILD_BUILD
            ),
            Test(
                name="clean_local_cache",
                repo_root_setup_command=CLEAN_REPOSITORY,
                setup_command=MSBUILD_RESTORE,
                test_command=QUICKBUILD_BUILD
            ),
            Test(
                name="incremental",
                test_command=QUICKBUILD_BUILD
            )
        ]
    ),
    TestSuite(
        name="msb",
        tests=[
            Test(
                name="clean",
                repo_root_setup_command=CLEAN_REPOSITORY,
                setup_command=MSBUILD_RESTORE,
                test_command=MSBUILD_BASELINE_BUILD
            ),
            Test(
                name="incremental",
                test_command=MSBUILD_BASELINE_BUILD
            )
        ]
    ),
    TestSuite(
        name="msb-qb-fu2d",
        tests=[
            Test(
                name="clean_remote_cache",
                repo_root_setup_command=Commands(
                    DELETE_QB_CACHE, CLEAN_REPOSITORY),
                setup_command=MSBUILD_RESTORE,
                test_command=MSBUILD_QB_FU2D_BUILD
            ),
            Test(
                name="clean_local_cache",
                repo_root_setup_command=CLEAN_REPOSITORY,
                setup_command=MSBUILD_RESTORE,
                test_command=MSBUILD_QB_FU2D_BUILD
            ),
            Test(
                name="incremental",
                test_command=MSBUILD_QB_FU2D_BUILD
            )
        ]
    ),
    TestSuite(
        name="msb-fu2d",
        tests=[
            Test(
                name="clean",
                repo_root_setup_command=CLEAN_REPOSITORY,
                setup_command=MSBUILD_RESTORE,
                test_command=MSBUILD_FU2D_BUILD
            ),
            Test(
                name="incremental",
                test_command=MSBUILD_FU2D_BUILD
            )
        ]
    )
]

assert BASELINE_MSBUILD_EXE.is_file()
assert CACHE_MSBUILD_EXE.is_file()
assert CACHE_INITIALIZATION_LOGGER_DLL.is_file()

# add msbuild to the path to make qb happy
os.environ["PATH"] = f"{str(BASELINE_MSBUILD_EXE.parent)}{os.pathsep}{os.environ['PATH']}"

repo_results = run_tests(REPOS, TEST_REPOS_ROOT, TEST_SUITES, repetitions=3)
write_results_to_csv(repo_results, Path("repo_results.csv"))
