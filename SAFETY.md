# SAFETY

These requirements take precedence over every other requirement in this
repository (`docs/development_spec.md` §3). Code that violates them is
never written, for any reason.

| ID | Requirement |
|---|---|
| SAF-1 | No serial transmission before milestone M3 is complete. The transmit path is blocked in code. |
| SAF-2 | Transmission is enabled only when the environment variable `LAURELL_TX_ENABLED=1` is set. The default is disabled. |
| SAF-3 | Every transmit function supports a `dry_run` argument whose default is `True`. |
| SAF-4 | Byte sequences whose meaning is not confirmed are never sent. Sendable frames are managed as an allowlist. |
| SAF-5 | Commands that may start the motor never run without a separate, explicit confirmation argument. |
| SAF-6 | Tests on the real device run only with the chuck empty and the lid closed. A person checks this; code cannot verify it. |
| SAF-7 | Wiring changes are made by a person with both the device and the PC powered off. |
| SAF-8 | No run command is implemented until the interlock status bits are decoded. |

## Enforcement in code

| ID | Where |
|---|---|
| SAF-1 | `laurell.safety.transmit_milestone_reached` is `False`; only the reviewed M4 change may flip it. |
| SAF-2 | `laurell.safety.require_transmit_allowed()` also requires `LAURELL_TX_ENABLED` to be exactly `1`. |
| SAF-3 | `SerialTransport.write(data, *, dry_run=True)` checks the gate first, then logs instead of sending by default. |
| SAF-4 to SAF-8 | Not yet reachable: no frame encoder or command exists before M4. |

`transport.py` and `safety.py` restate these requirements in their module
docstrings, as the specification requires.

## Source text

`docs/development_spec.md` §3, verbatim. The English table above is a
translation; if the two ever disagree, this text governs.

| ID | 요구사항 |
|---|---|
| SAF-1 | 마일스톤 M3 완료 이전에는 시리얼 송신을 수행하지 않습니다. 코드 레벨에서 송신 경로를 차단합니다 |
| SAF-2 | 송신 기능은 환경변수 `LAURELL_TX_ENABLED=1`이 설정된 경우에만 활성화합니다. 기본값은 비활성입니다 |
| SAF-3 | 모든 송신 함수는 `dry_run` 인자를 지원하며 기본값은 `True`입니다 |
| SAF-4 | 의미가 확정되지 않은 바이트열은 전송하지 않습니다. 송신 가능 프레임은 allowlist로 관리합니다 |
| SAF-5 | 모터 기동 가능성이 있는 명령은 별도의 명시적 확인 인자 없이는 실행하지 않습니다 |
| SAF-6 | 실기기 대상 시험은 척을 비우고 리드를 닫은 상태에서만 수행합니다. 이 조건은 사람이 확인하며 코드가 검증할 수 없습니다 |
| SAF-7 | 결선 변경은 장비와 PC 양쪽 전원을 끈 상태에서 사람이 수행합니다 |
| SAF-8 | 인터록 상태 비트가 해석되기 전까지는 어떠한 실행 명령도 구현하지 않습니다 |
