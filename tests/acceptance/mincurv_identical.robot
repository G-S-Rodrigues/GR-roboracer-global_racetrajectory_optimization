*** Settings ***
Library     tumfork_keywords.keywords
Library     OperatingSystem
Library     Collections

*** Variables ***
@{CURV_TYPES}       shortest_path    mincurv    mincurv_iqp
@{VEHICLES}         f1tenth_default    f1tenth_gym_limits

*** Test Cases ***
TUMFORK-4010 min-curv output is byte-identical to upstream
    [Documentation]    The three non-time optimizers return the same four values
    ...    as unmodified ForzaETH b1b38ec, in one container, with the ini
    ...    GR-roboracer renders for each vehicle.
    [Tags]    fast
    ${tmp} =    Evaluate    __import__("tempfile").mkdtemp()
    FOR    ${vehicle}    IN    @{VEHICLES}
        ${case} =    Make Oval Case    ${tmp}/${vehicle}    ${vehicle}
        FOR    ${curv}    IN    @{CURV_TYPES}
            ${up} =    Run Upstream Solve    ${case}    ${curv}    ${tmp}/${vehicle}-${curv}-up.npz
            ${br} =    Run Branch Solve    ${case}    ${curv}    ${tmp}/${vehicle}-${curv}-br.npz
            Package File Should Start With    ${br}    /ws/
            Package File Should Start With    ${up}    /opt/upstream/
            Solutions Should Be Identical    ${br}    ${up}    ${curv} ${vehicle}
        END
    END
