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
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4040.npz    ${WORK}/export-4040
    ...    timeout=900    max_wall_time_s=20
    Log    setup+solve wall ${r}[wall_s] s
    Should Be Equal As Integers    ${r}[rc]    1    ${r}[stderr]
    Should Contain    ${r}[stdout]    MINTIME_NOT_CONVERGED
    Should Be Equal    ${r}[status][status]    stopped_wall_time
    Should Be True    ${r}[status][wall_time_s] <= 30
    FOR    ${name}    IN    w0    lam_x0
        ${n} =    Count Lines In File    ${r}[state_dir]/${name}.csv
        Should Be Equal As Integers    ${{(${n} - 5) % 24}}    0
    END
    File Should Exist    ${r}[state_dir]/lam_g0.csv
    Directory Should Not Exist    /ws/global_racetrajectory_optimization/outputs/mintime

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
    ${r} =    Run Mintime Solve    ${case}    ${WORK}/4050.npz    ${WORK}/export-4050
    ...    timeout=900    warm_start_dir=${WORK}/export-4040/mintime    max_iter=5
    Should Be Equal    ${r}[status][x0_source]    warm_start_dir
    ${saved_f} =    Set Variable    ${cold}[objective]
    ${d_warm} =    Evaluate    abs(${r}[status][iteration0_objective] - ${saved_f})
    ${d_cold} =    Evaluate    abs(${cold}[iteration0_objective] - ${saved_f})
    Should Be True    ${d_warm} < ${d_cold}    warm ${d_warm} vs cold ${d_cold}
