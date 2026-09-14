# Laurell WS-650 자동화 개발사양서

프로젝트명: laurell-ws650-ctl
작성일: 2026년 9월 14일
대상 장비: Laurell WS-650MZ-23NPP/LITE, 650 Series Controller, 보드 P/N 15000018 REV. C
실행 주체: Claude Code
참조 문서: `serial_protocol_reference.md`, `laurell_ws650_serial_protocol_brief.md`

---

## 1. 목표

RS-232 포트를 통해 스핀코터를 프로그래밍 방식으로 제어하고 상태를 수집하는 Python 패키지를 개발합니다. 명령어 세트가 비공개이므로 역공학 단계와 제품화 단계를 분리해 진행합니다.

최종 산출물은 다음 세 가지입니다.

| 산출물 | 내용 |
|---|---|
| 프로토콜 명세 | 역공학으로 확정한 프레임 구조와 명령 목록을 문서화 |
| 드라이버 라이브러리 | 프로토콜을 캡슐화한 Python 패키지 |
| 자동화 레이어 | 레시피 실행, 로깅, 상위 시스템 연동 인터페이스 |

---

## 2. 범위

### 2.1 포함

| 항목 |
|---|
| 시리얼 포트 캡처 및 보율 자동 탐색 |
| 프레임 경계 및 필드 구조 분석 도구 |
| 장비 조작과 수신 데이터의 시간 상관 분석 |
| 확정된 프로토콜의 인코더 및 디코더 |
| 상태 폴링 및 이벤트 스트림 API |
| 레시피 조회, 전송, 원격 실행 API |
| 구조화 로깅 및 실행 기록 저장 |

### 2.2 제외

| 항목 | 사유 |
|---|---|
| 펌웨어 수정 | 장비 보증 및 안전 문제 |
| I2C 확장 버스 제어 | 별도 커넥터이며 이번 범위 밖 |
| Spin 3000 바이너리 재배포 | 라이선스 문제 |
| 안전 인터록 우회 | 절대 금지 |

---

## 3. 안전 요구사항

이 절의 요구사항은 다른 모든 요구사항에 우선합니다. 위반하는 코드는 어떤 이유로도 작성하지 않습니다.

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

Claude Code는 위 요구사항을 `SAFETY.md`로 저장소 루트에 복제하고, 송신 관련 모듈 상단에 주석으로 재기재합니다.

---

## 4. 현재 확정 사실

개발 착수 시점의 전제입니다. 미확정 항목은 사람이 실측으로 채웁니다.

| 항목 | 값 | 상태 |
|---|---|---|
| 트랜시버 | U18, SP3232EE, 16핀 TSSOP | 확정 |
| 장비 TXD 배선 | 녹색, SP3232E 14번 T1OUT | 확정 |
| 장비 RXD 배선 | 노란색, SP3232E 13번 R1IN | 확정 |
| 접지 배선 | 검정색 추정 | 미확정 |
| 4번째 배선 | 분홍색 또는 빨강, 정체 미상 | 미확정 |
| 보율 | 미상 | 미확정 |
| 프레임 형식 | 미상 | 미확정 |
| USB 컨버터 | NETmate KW-525, PL-2303, DB9 수커넥터 | 확정 |

---

## 5. 개발 환경

| 항목 | 값 |
|---|---|
| 언어 | Python 3.11 이상 |
| 패키지 관리 | uv 또는 pip와 venv |
| 핵심 의존성 | pyserial |
| 분석 의존성 | numpy, matplotlib |
| 개발 의존성 | pytest, pytest-cov, ruff, mypy |
| 대상 OS | Windows 및 Linux 양쪽 |
| 포트 표기 | Windows는 `COM3` 형식, Linux는 `/dev/ttyUSB0` 형식 |

---

## 6. 저장소 구조

```
laurell-ws650-ctl/
  README.md
  SAFETY.md
  pyproject.toml
  docs/
    serial_protocol_reference.md
    hardware_findings.md
    protocol_spec.md
  src/laurell/
    __init__.py
    transport.py
    capture.py
    baudscan.py
    framing.py
    checksum.py
    codec.py
    driver.py
    recipes.py
    safety.py
    cli.py
  analysis/
    notebooks/
    scripts/
  captures/
    .gitkeep
  tests/
    test_checksum.py
    test_framing.py
    test_codec.py
    fixtures/
```

`captures/` 는 실기기에서 수집한 원시 데이터 보관 장소입니다. 용량이 커질 수 있으므로 `.gitignore`에 대용량 확장자를 등록하되, 분석 근거가 되는 대표 샘플은 `tests/fixtures/`로 복사해 버전 관리합니다.

---

## 7. 마일스톤

각 마일스톤은 수용 기준을 모두 충족해야 다음 단계로 넘어갑니다. 실기기 조작이 필요한 항목은 사람이 수행하고 결과 파일을 저장소에 투입합니다.

### M0. 프로젝트 스캐폴딩

| 구분 | 내용 |
|---|---|
| 작업 | 저장소 구조 생성, `pyproject.toml` 작성, ruff 및 mypy 설정, `SAFETY.md` 작성, `transport.py`에 수신 전용 래퍼 구현 |
| 사람 작업 | 없음 |
| 수용 기준 | `ruff check`와 `mypy src` 무오류, `pytest` 실행 성공, `transport.py`의 송신 메서드가 `SAFETY.md` 조건 미충족 시 예외 발생 |

`transport.py` 요구사항입니다.

| 요구 | 내용 |
|---|---|
| 클래스명 | `SerialTransport` |
| 생성자 인자 | `port`, `baudrate`, `bytesize`, `parity`, `stopbits`, `timeout` |
| 개방 동작 | 개방 직후 DTR과 RTS를 내림 |
| 송신 차단 | `write` 호출 시 `LAURELL_TX_ENABLED` 미설정이면 `TransmitBlockedError` 발생 |
| 컨텍스트 매니저 | `with` 문 지원, 종료 시 포트 확실히 반납 |

### M1. 수신 캡처와 보율 자동 탐색

| 구분 | 내용 |
|---|---|
| 작업 | `capture.py`와 `baudscan.py` 구현, CLI 서브커맨드 `scan`과 `capture` 추가 |
| 사람 작업 | DB9 암커넥터 제작, 장비 TXD와 SG만 결선, 장비 전원 인가 후 스캔 실행 |
| 수용 기준 | 보율 후보별 점수표 출력, 최고 점수 조합에서 인쇄 가능 ASCII 비율 90 퍼센트 이상 또는 반복 주기 구조 검출 |

`baudscan.py` 판정 로직 요구사항입니다.

| 지표 | 계산 | 가중치 |
|---|---|---|
| 인쇄 가능 ASCII 비율 | 0x20에서 0x7E 및 0x09, 0x0A, 0x0D 의 비율 | 높음 |
| 프레이밍 에러 빈도 | pyserial이 보고하는 에러 수, 지원되지 않으면 생략 | 중간 |
| 바이트 간격 히스토그램 군집성 | 간격 분포의 이봉성 여부 | 중간 |
| 반복 바이트열 검출 | 길이 4 이상 부분열의 재출현 주기 | 높음 |
| 널 바이트 및 0xFF 비율 | 높으면 감점 | 낮음 |

탐색 대상 조합은 보율 5종에 형식 4종을 곱한 20가지입니다. 각 조합당 최소 5초 수집합니다.

캡처 파일 형식은 JSON Lines이며 한 줄이 한 이벤트입니다.

```json
{"ts": 1789350049.123456, "dir": "rx", "hex": "02 31 32 03 41", "ascii": ".12.A", "gap_us": 104}
```

| 필드 | 의미 |
|---|---|
| `ts` | UNIX 시각, 소수 6자리 |
| `dir` | `rx` 또는 `tx` |
| `hex` | 공백 구분 16진 바이트열 |
| `ascii` | 인쇄 불가 문자는 마침표로 치환 |
| `gap_us` | 직전 바이트와의 간격, 마이크로초 |

세션 메타데이터는 같은 디렉터리의 `session.json`에 저장합니다.

| 키 | 내용 |
|---|---|
| `port`, `baudrate`, `bytesize`, `parity`, `stopbits` | 통신 파라미터 |
| `started_at`, `ended_at` | ISO 8601 |
| `operator_notes` | 사람이 기록한 장비 조작 내역 |
| `firmware`, `serial_number`, `model` | 컨트롤러 About 화면에서 읽은 값 |

### M2. 프레임 경계 분해

| 구분 | 내용 |
|---|---|
| 작업 | `framing.py`와 `checksum.py` 구현, 분석 스크립트로 후보 구조 탐색 |
| 사람 작업 | 없음. M1 캡처 데이터로 진행 |
| 수용 기준 | 캡처의 95 퍼센트 이상 바이트가 프레임으로 분해됨, 체크섬 후보가 전 프레임에서 일관되게 검증되거나 체크섬 없음이 근거와 함께 결론 |

`framing.py` 요구사항입니다.

| 함수 | 역할 |
|---|---|
| `split_by_idle(events, idle_us)` | 무음 구간 기준 분할 |
| `split_by_delimiter(data, start, end)` | 델리미터 기준 분할 |
| `split_by_length_field(data, offset, size, endian)` | 길이 필드 기준 분할 |
| `score_split(frames)` | 길이 분포 일관성과 잔여 바이트 비율로 점수화 |

`checksum.py`는 참조 문서 8절의 알고리즘 전체를 구현하고, 프레임 목록에 대해 모든 알고리즘과 모든 검증 범위 조합을 전수 시도하는 `find_checksum(frames)` 함수를 제공합니다. ASCII 16진 인코딩 형태도 함께 시도합니다.

### M3. 필드 의미 매핑

| 구분 | 내용 |
|---|---|
| 작업 | 상관 분석 도구 작성, `docs/protocol_spec.md` 초안 작성 |
| 사람 작업 | 정해진 시나리오대로 장비를 조작하며 조작 시각을 기록. 캡처와 함께 제출 |
| 수용 기준 | 인터록, 진공, RPM, 프로그램 번호에 해당하는 필드 위치와 인코딩을 각각 특정 |

사람이 수행할 조작 시나리오입니다. 각 동작 사이에 5초 이상 간격을 둡니다.

| 순번 | 조작 | 관찰 목적 |
|---|---|---|
| 1 | 전원 인가 후 30초 대기 | 부팅 배너, 모델명, 시리얼 번호 문자열 |
| 2 | 리드 열기, 닫기 3회 반복 | 인터록 상태 비트 |
| 3 | 진공 on, off 3회 반복 | 진공 상태 비트 및 진공도 수치 |
| 4 | 프로그램 번호를 1에서 5까지 순차 변경 | 인덱스 필드 |
| 5 | 500 rpm 30초 실행 | RPM 수치 필드의 선형성 |
| 6 | 1000 rpm 30초 실행 | 동일 |
| 7 | 2000 rpm 30초 실행 | 동일 |
| 8 | 실행 중 일시정지 후 재개 | 실행 상태 머신 |

5번부터 8번은 척을 비운 상태에서 수행합니다.

분석 도구 요구사항입니다.

| 기능 | 내용 |
|---|---|
| 바이트 위치별 엔트로피 | 고정 필드와 가변 필드 구분 |
| 조작 시각과의 시간 정렬 | 조작 전후 변화 바이트 추출 |
| 수치 필드 후보 검증 | 1바이트, 2바이트 LE 및 BE, ASCII 10진 문자열, BCD 각각 시도 |
| 비트 플래그 후보 검증 | 바이트 내 개별 비트와 조작의 상관 |

`docs/protocol_spec.md` 형식입니다.

| 절 | 내용 |
|---|---|
| 프레임 구조 | 헤더, 길이, 타입, 페이로드, 체크섬의 오프셋과 크기 |
| 메시지 타입 표 | 타입 코드와 의미 |
| 상태 메시지 필드 표 | 오프셋, 크기, 인코딩, 의미, 단위 |
| 미해석 필드 | 아직 의미를 모르는 오프셋 목록 |
| 근거 | 각 결론을 뒷받침하는 캡처 파일명과 프레임 번호 |

### M4. 송신 시험

이 단계부터 SAF-1의 제약이 해제되지만 SAF-2에서 SAF-8은 계속 적용됩니다.

| 구분 | 내용 |
|---|---|
| 작업 | `codec.py` 인코더 구현, 안전한 순서로 송신 시험 |
| 사람 작업 | RXD 배선 연결, 시험 중 장비 상시 감시, 비상 정지 준비 |
| 수용 기준 | 조회성 명령 최소 1종에 대해 재현 가능한 응답 확보 |

송신 시도 순서입니다. 각 단계에서 예기치 않은 장비 반응이 있으면 즉시 중단합니다.

| 순번 | 전송 내용 | 근거 |
|---|---|---|
| 1 | CR 1바이트 | 프롬프트 또는 에코 반응 확인 |
| 2 | CRLF | 동일 |
| 3 | ENQ 0x05 | 상태 조회 관행 |
| 4 | 수신한 상태 프레임을 그대로 반사 | 응답 여부 확인 |
| 5 | M3에서 확정한 구조로 만든 조회 프레임 | Model Number 및 Serial Number 조회 추정 |

모터 기동 가능성이 있는 프레임은 이 단계에서 전송하지 않습니다.

### M5. 드라이버 API

| 구분 | 내용 |
|---|---|
| 작업 | `driver.py` 구현, 상태 폴링 및 이벤트 스트림, 예외 계층 정의 |
| 사람 작업 | 실기기 연동 시험 |
| 수용 기준 | 상태 조회가 10분 연속 무오류, 통신 단절 시 자동 재연결, 모든 공개 메서드에 타입 힌트와 독스트링 |

공개 API 초안입니다. 실제 시그니처는 M3 결과에 따라 조정합니다.

```python
class SpinCoater:
    def __init__(self, port: str, baudrate: int, *, timeout: float = 1.0) -> None: ...
    def __enter__(self) -> "SpinCoater": ...
    def __exit__(self, *exc: object) -> None: ...

    @property
    def info(self) -> ControllerInfo: ...
    def read_status(self) -> Status: ...
    def stream_status(self) -> Iterator[Status]: ...
    def list_programs(self) -> list[ProgramSummary]: ...
    def read_program(self, index: int) -> Program: ...
    def write_program(self, index: int, program: Program, *, dry_run: bool = True) -> None: ...
    def start(self, index: int, *, confirm: bool = False, dry_run: bool = True) -> None: ...
    def stop(self, *, dry_run: bool = True) -> None: ...
```

데이터 클래스 초안입니다.

| 클래스 | 필드 |
|---|---|
| `ControllerInfo` | `model`, `serial_number`, `firmware`, `controller_rev` |
| `Status` | `timestamp`, `rpm`, `vacuum_kpa`, `lid_closed`, `vacuum_on`, `running`, `program_index`, `step_index`, `elapsed_s`, `raw` |
| `ProgramSummary` | `index`, `name`, `step_count` |
| `Program` | `index`, `name`, `steps` |
| `Step` | `seconds`, `rpm`, `accel_rpm_s`, `outputs` |

예외 계층입니다.

| 예외 | 발생 조건 |
|---|---|
| `LaurellError` | 최상위 |
| `TransportError` | 포트 개방 실패, 단절 |
| `TransmitBlockedError` | 안전 조건 미충족 상태의 송신 시도 |
| `ProtocolError` | 프레임 파싱 실패, 체크섬 불일치 |
| `TimeoutError` | 응답 대기 초과 |
| `DeviceStateError` | 인터록 미충족 등 장비 상태로 인한 거부 |

`Status.raw`에는 원시 프레임을 항상 보존합니다. 미해석 필드가 남아 있는 동안 디버깅에 필요합니다.

### M6. 자동화 레이어

| 구분 | 내용 |
|---|---|
| 작업 | `recipes.py` 구현, 레시피 파일 포맷 정의, 실행 기록 저장 |
| 사람 작업 | 실제 공정 조건으로 검증 |
| 수용 기준 | 레시피 파일로 정의한 공정이 장비 내부 프로그램과 동일하게 실행됨, 실행 기록이 시각과 함께 저장됨 |

레시피 파일은 YAML을 사용합니다.

```yaml
name: pmma_2000rpm
description: PMMA 표준 코팅
steps:
  - seconds: 5
    rpm: 500
    accel_rpm_s: 500
  - seconds: 30
    rpm: 2000
    accel_rpm_s: 1000
  - seconds: 5
    rpm: 0
    accel_rpm_s: 1000
```

---

## 8. CLI 설계

진입점은 `laurell` 입니다.

| 커맨드 | 인자 | 기능 |
|---|---|---|
| `laurell ports` | 없음 | 사용 가능한 시리얼 포트 목록 |
| `laurell scan` | `--port`, `--seconds` | 보율 및 형식 자동 탐색, 점수표 출력 |
| `laurell capture` | `--port`, `--baud`, `--format`, `--out` | 수신 전용 캡처, JSONL 저장 |
| `laurell analyze frames` | `--capture` | 프레임 분해 후보 출력 |
| `laurell analyze checksum` | `--capture` | 체크섬 알고리즘 전수 검증 |
| `laurell analyze correlate` | `--capture`, `--events` | 조작 기록과 상관 분석 |
| `laurell status` | `--port`, `--baud` | 현재 상태 1회 출력 |
| `laurell watch` | `--port`, `--baud` | 상태 연속 출력 |
| `laurell run` | `--recipe`, `--confirm` | 레시피 실행. 기본은 dry run |

`--confirm` 없이 실행되는 `run`은 전송할 프레임을 출력만 하고 종료합니다.

---

## 9. 테스트 전략

실기기가 없는 상태에서도 개발이 진행되어야 하므로, 캡처 데이터를 픽스처로 고정합니다.

| 대상 | 방법 |
|---|---|
| `checksum.py` | 알려진 테스트 벡터로 각 알고리즘 검증. CRC-16/MODBUS는 입력 `123456789`에 대해 0x4B37 |
| `framing.py` | 합성 프레임과 실제 캡처 픽스처로 분해 결과 검증 |
| `codec.py` | 인코딩 후 디코딩 결과가 원본과 일치하는 왕복 테스트 |
| `transport.py` | pyserial을 모킹해 송신 차단 로직 검증 |
| `driver.py` | 캡처 데이터를 재생하는 페이크 트랜스포트로 통합 테스트 |

커버리지 목표는 `src/laurell` 기준 80 퍼센트입니다. 실기기 의존 테스트는 `@pytest.mark.hardware`로 표시하고 기본 실행에서 제외합니다.

---

## 10. Claude Code 작업 규칙

| ID | 규칙 |
|---|---|
| WR-1 | 한 번에 한 마일스톤만 진행합니다. 마일스톤 수용 기준을 충족하기 전에 다음 단계 코드를 작성하지 않습니다 |
| WR-2 | 실기기 조작이 필요한 작업은 직접 수행하려 하지 말고, 사람이 수행할 절차를 명확히 제시하고 결과 파일을 기다립니다 |
| WR-3 | 프로토콜에 관한 추측은 코드 주석이 아니라 `docs/protocol_spec.md`의 미확정 절에 기록합니다 |
| WR-4 | 확정되지 않은 필드 해석을 기본 동작에 반영하지 않습니다. 원시 데이터는 항상 보존합니다 |
| WR-5 | 커밋은 마일스톤 단위가 아니라 기능 단위로 잘게 나눕니다 |
| WR-6 | 외부 네트워크에서 Laurell 관련 비공개 자료를 내려받으려 시도하지 않습니다 |
| WR-7 | 안전 요구사항 3절을 완화하는 방향의 리팩터링은 제안하지 않습니다 |
| WR-8 | 캡처 파일에서 장비 시리얼 번호가 발견되면 공개 저장소 커밋 전에 마스킹 여부를 사람에게 확인합니다 |

---

## 11. 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| 보율 탐색 실패 | M1 정체 | 로직 애널라이저로 비트 폭 실측. 참조 문서 11절 설정 적용 |
| 프로토콜이 이진 독자 규격 | M2와 M3 장기화 | Spin 3000을 제조사에서 받아 가상 COM 포트 스니퍼로 정상 통신 캡처 |
| 4번째 배선이 전원선 | 결선 시 손상 | 확정 전까지 미결선 원칙 유지 |
| 컨트롤러가 수동 수신만 하고 주기 송출을 안 함 | M1에서 데이터 없음 | 펌웨어 버전 확인. 47000022y 이후 버전은 원격 명령 수신 중 주기 송출을 중단하므로, 아무 명령도 보내지 않은 상태에서 재시도 |
| PL-2303 드라이버 문제 | 전 단계 차단 | 루프백 시험을 선행. 실패 시 FTDI 계열 컨버터로 교체 |
| 역공학으로 확정 불가 | 프로젝트 중단 | support@laurell.com 에 통신 사양 공식 요청. 제조사가 평생 무상 지원을 명시하고 있음 |

---

## 12. 착수 지시

Claude Code는 다음 순서로 시작합니다.

1. 저장소를 초기화하고 6절 구조를 생성합니다.
2. 3절을 그대로 `SAFETY.md`에 기록합니다.
3. 4절을 `docs/hardware_findings.md`에 기록하고, 인수인계 문서와 참조 문서를 `docs/`에 복사합니다.
4. M0 수용 기준을 충족하는 스캐폴딩과 `transport.py`를 구현합니다.
5. M1의 `baudscan.py`와 `capture.py`를 구현하고, 사람이 수행할 결선 및 실행 절차를 체크리스트로 출력합니다.
6. 사람의 캡처 결과 투입을 기다립니다.
