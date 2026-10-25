*** Settings ***
Library     tumfork_keywords.keywords
Library     OperatingSystem
Library     Collections

*** Variables ***
${WORK}             ${OUTPUT DIR}/mintime-work

*** Test Cases ***
TUMFORK-4040 a cold min-time solve with a wall limit stops, saves state and says so
    [Documentation]    max_wall_time_s=20 on the Spielberg gym 0.40 fixture:
    ...    MintimeNotConverged (exit 1), solver_status.json says stopped_wall_time
    ...    with a wall time counted from the solver call, and the three state files
    ...    hold nx + N*24 values.
    [Tags]    fast
    ${case} =    Make Gym Case    ${WORK}/gym
    Remove Directory    ${WORK}/export-4040    recursive=True
    ${before} =    Snapshot Package Outputs
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4040.npz    ${WORK}/export-4040
    ...    timeout=900    max_wall_time_s=20
    Log    setup+solve wall ${r}[wall_s] s
    Should Be Equal As Integers    ${r}[rc]    1    ${r}[stderr]
    Should Contain    ${r}[stdout]    MINTIME_NOT_CONVERGED
    Should Be Equal    ${r}[status][status]    stopped_wall_time
    Should Be True    ${r}[status][wall_time_s] <= 30
    FOR    ${name}    IN    w0    lam_x0
        ${n} =    Evaluate    len(open($r['state_dir'] + '/' + $name + '.csv').read().split())
        Should Be Equal As Integers    ${{(${n} - 5) % 24}}    0
    END
    File Should Exist    ${r}[state_dir]/lam_g0.csv
    Package Outputs Should Be Unchanged    ${before}

TUMFORK-4050 resume from the saved state starts nearer the saved objective than a cold start
    [Documentation]    From 4040's state, solver_status.json records x0_source
    ...    warm_start_dir and iteration 0 starts nearer the objective saved at the
    ...    stop than a cold start's iteration 0 does (the bound push moves x, so
    ...    equality is not expected).
    [Tags]    fast
    ${have} =    Run Keyword And Return Status    File Should Exist    ${WORK}/export-4040/mintime/w0.csv
    Run Keyword If    not ${have}    Fail    no saved state: run TUMFORK-4040 first
    ${saved} =    Get File    ${WORK}/export-4040/mintime/solver_status.json
    ${cold} =    Evaluate    json.loads($saved)    json
    ${case} =    Make Gym Case    ${WORK}/gym
    ${before} =    Snapshot Package Outputs
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4050.npz    ${WORK}/export-4050
    ...    timeout=900    warm_start_dir=${WORK}/export-4040/mintime    max_iter=5
    Should Be Equal    ${r}[status][x0_source]    warm_start_dir
    ${saved_f} =    Set Variable    ${cold}[objective]
    ${d_warm} =    Evaluate    abs(${r}[status][iteration0_objective] - ${saved_f})
    ${d_cold} =    Evaluate    abs(${cold}[iteration0_objective] - ${saved_f})
    Should Be True    ${d_warm} < ${d_cold}    warm ${d_warm} vs cold ${d_cold}

TUMFORK-4030 seeded min-time on Spielberg gym 0.40 reproduces S1c
    [Documentation]    R-SEED settings (mu_init 1e-3, seed, 3 threads): Optimal,
    ...    lap 32.3328 +- 1e-3 s (closed TUM lap), closure < 1e-4, solver_status.json written.
    ...    The iteration count is recorded in the log (S1c took 1715).
    [Tags]    heavy
    ${case} =    Make Gym Case    ${WORK}/gym
    Remove Directory    ${WORK}/export-4030    recursive=True
    ${before} =    Snapshot Package Outputs
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4030.npz    ${WORK}/export-4030
    ...    timeout=7200    seed=True    mu_init=1e-3
    Should Be Equal As Integers    ${r}[rc]    0    ${r}[stderr]
    Log    iterations ${r}[status][iterations], solve wall ${r}[status][wall_time_s] s
    Should Be Equal    ${r}[status][status]    Solve_Succeeded
    # Reference 32.3328 s: TUM's closed lap, ruling 2026-10-25. The harness lap
    # that gave 32.3268 (STEP1/solve3.py:147, an open left Riemann sum over the
    # 3387-row post line) omitted the closing element, 0.1 m / 16.2 m/s = 6.2e-3 s.
    Should Be True    abs(${r}[arrays][lap_time] - 32.3328) <= 1e-3
    ${c} =    Closure Error    ${r}
    Should Be True    ${c} < 1e-4    closure ${c}
    Create File    ${WORK}/4030.lap    ${r}[arrays][lap_time]
    Package Outputs Should Be Unchanged    ${before}

TUMFORK-4020 seeded min-time on the oval converges and its s closes
    [Documentation]    The oval, seeded from its own min-curv line at mu_init 1e-3:
    ...    exit 0, Solve_Succeeded, closure < 1e-4, and no outputs/ in the package.
    [Tags]    fast
    ${case} =    Make Oval Mintime Case    ${WORK}/oval
    Remove Directory    ${WORK}/export-4020    recursive=True
    ${before} =    Snapshot Package Outputs
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4020.npz    ${WORK}/export-4020
    ...    timeout=1500    seed=True    mu_init=1e-3
    Should Be Equal As Integers    ${r}[rc]    0    ${r}[stderr]
    Log    iterations ${r}[status][iterations], solve wall ${r}[status][wall_time_s] s, total ${r}[wall_s] s
    Should Be Equal    ${r}[status][status]    Solve_Succeeded
    ${c} =    Closure Error    ${r}
    Should Be True    ${c} < 1e-4    closure ${c}
    Package Outputs Should Be Unchanged    ${before}

TUMFORK-4050h resume from 4030's converged state converges to the same lap
    [Documentation]    From 4030's saved state, warm_start_dir: same lap (1e-6),
    ...    iterations <= 1188, which is 2x the 594 measured once in gr-tum-dev on 2026-10-25
    ...    (TUM's default warm start pushes bounds and mu by 1e-3, so a resume is not instant).
    [Tags]    heavy
    ${case} =    Make Gym Case    ${WORK}/gym
    Remove Directory    ${WORK}/export-4050h    recursive=True
    ${before} =    Snapshot Package Outputs
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4050h.npz    ${WORK}/export-4050h
    ...    timeout=3600    warm_start_dir=${WORK}/export-4030/mintime
    Should Be Equal As Integers    ${r}[rc]    0    ${r}[stderr]
    Log    resume iterations ${r}[status][iterations], lap ${r}[arrays][lap_time]
    Should Be Equal    ${r}[status][x0_source]    warm_start_dir
    ${ref} =    Get File    ${WORK}/4030.lap
    Should Be True    abs(${r}[arrays][lap_time] - ${ref}) <= 1e-6
    Should Be True    ${r}[status][iterations] <= 1188    2x the measured 594
