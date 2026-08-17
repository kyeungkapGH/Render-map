# Render Map

MapLibre GL JS와 PMTiles(벡터 타일)를 사용한 웹 지도 시각화 프로젝트입니다.
지도 스타일은 [Protomaps](https://protomaps.com) 오픈소스 베이스맵을 사용합니다.

## 시작하기

빌드 도구 없이 정적 파일만으로 동작합니다. 다만 브라우저가 `fetch`로 로컬 JS
모듈과 타일을 읽어와야 하므로 `file://`로 직접 열지 말고 로컬 서버로 실행하세요.

```bash
python3 -m http.server 8000
```

이후 브라우저에서 `http://localhost:8000` 접속.

## 구조

- `index.html` — 지도 페이지. MapLibre GL CSS와 vendor 스크립트를 불러옵니다.
- `map.js` — 지도 초기화 로직 (ES 모듈). PMTiles 프로토콜 등록, Protomaps
  베이스맵 스타일 구성, 마커 표시.
- `vendor/maplibre-gl/` — [MapLibre GL JS](https://maplibre.org/maplibre-gl-js/docs/) (지도 렌더링, WebGL 기반)
- `vendor/pmtiles/` — [PMTiles](https://docs.protomaps.com/pmtiles/) (단일 파일 벡터 타일 아카이브를 브라우저에서 직접 읽는 라이브러리)
- `vendor/basemaps/` — [@protomaps/basemaps](https://github.com/protomaps/basemaps) (Protomaps 베이스맵 스타일 레이어 생성기)
- `data/country-borders.geojson`, `data/state-borders.geojson` — 우크라이나, 레바논, 이스라엘, 예멘, 이란의 국경선/주(州) 경계선.
- `scripts/build-borders.py` — 위 두 GeoJSON을 다시 만드는 스크립트.

라이브러리는 CDN 대신 `npm install`로 받아서 이 저장소 안에 직접 vendoring
했습니다. 버전을 올리려면 `npm install maplibre-gl@latest pmtiles@latest
@protomaps/basemaps@latest`로 받은 뒤 각 `dist/` 산출물을 `vendor/` 아래
같은 파일명으로 복사하면 됩니다.

## 타일 데이터에 대해

`map.js`의 `PMTILES_URL`은 현재 Protomaps 베이스맵을 미러링하는
[Source Cooperative](https://source.coop/protomaps/openstreetmap)의
공개 PMTiles 파일(`https://data.source.coop/protomaps/openstreetmap/v4.pmtiles`)을
가리킵니다.

**CORS 주의**: Protomaps의 데모 버킷(`demo-bucket.protomaps.com`)과
source.coop 둘 다 공식적으로는 "다른 사이트에서 바로 hotlink하지 말라"고
안내합니다 — 실제로 데모 버킷은 `Access-Control-Allow-Origin` 헤더가 없어서
GitHub Pages처럼 다른 도메인에 배포하면 브라우저가 요청을 그냥 막아버립니다
(Network 탭엔 `status 0`, `type unknown`으로 뜸). source.coop 쪽이 실제로
동작하는지는 이 저장소를 배포해서 직접 확인해야 합니다(로컬 개발 샌드박스
네트워크 정책상 이 도메인들에 접속해 직접 검증하지 못했습니다).

**결국 가장 확실한 방법은 자체 호스팅**입니다. PMTiles 파일을 이 저장소
안에(`vendor/`처럼) 넣어서 GitHub Pages로 같이 서빙하면, 같은 오리진이라
CORS 문제 자체가 사라집니다:

- [maps.protomaps.com](https://maps.protomaps.com)에서 원하는 지역만
  추출한 PMTiles를 다운로드하거나
- [Planetiler](https://github.com/onthegomap/planetiler)로 직접 빌드한 뒤
- 저장소에 커밋하고 `map.js`의 `PMTILES_URL`을 그 파일 경로(예:
  `./data/seoul.pmtiles`)로 바꾸면 됩니다. (GitHub 저장소 파일 하나는
  100MB를 넘으면 안 되므로, 전세계가 아니라 필요한 지역만 추출하는 걸
  권장합니다.)

## 배포

`claude/project-getting-started-5dwqgf` 브랜치에 푸시하면 `.github/workflows/deploy-pages.yml`
워크플로가 자동으로 GitHub Pages에 배포합니다.

최초 1회, 저장소 **Settings → Pages → Build and deployment → Source**를
`GitHub Actions`로 설정해야 워크플로가 실제로 페이지를 게시할 수 있습니다.

배포되면 다음 주소에서 확인할 수 있습니다:
`https://kyeungkapgh.github.io/Render-map/`

## 국경선 / 주 경계 오버레이

`map.js`는 베이스맵 위에 `data/country-borders.geojson`(국경선, 굵은 실선)과
`data/state-borders.geojson`(주/도 경계, 진한 회색 점선)을 얹습니다.
색은 `map.js`의 `BORDER_COLOR`/`STATE_BORDER_COLOR`에서 바꿉니다.

베이스맵이 원래 그리는 국경선 레이어(`boundaries_country`, `boundaries`)는
스타일에서 빼두었습니다. Protomaps의 `boundaries` 소스레이어에는 경계선마다
행정구역 등급(`kind`/`kind_detail`)만 있고 어느 나라 소속인지 식별하는
필드가 없어서 이 5개국만 골라 강조할 수가 없기 때문입니다. 그 대신 이
GeoJSON 오버레이가 유일한 경계선이 되고, 5개국 외 지역엔 국경선이 그려지지
않는 트레이드오프가 있습니다.

### 왜 데이터 출처가 두 개인가

선이 베이스맵과 어긋나 보이는 문제는 대부분 **해안선**에서 생깁니다.
Natural Earth는 1:10m 축척으로 일반화된 데이터라 해안선이 OSM 기반 베이스맵과
수 km씩 차이가 나기 때문입니다. 그래서 두 파일의 출처를 나눴습니다:

- **국경선**은 [@geo-maps/countries-land](https://github.com/simonepri/geo-maps)
  (OSM에서 생성 후 OSM 해안선으로 클리핑됨)를 씁니다. 베이스맵과 같은
  혈통이라 해안선이 어긋나지 않습니다.
- **주 경계**는 마땅한 OSM 계보 데이터가 없어 Natural Earth Admin-1을 쓰되,
  **인접한 두 주가 공유하는 변만** 뽑아 씁니다. 바깥 테두리는 아무와도
  공유되지 않으므로 애초에 나오지 않습니다. 내부 경계선은 베이스맵에
  대응하는 선이 없어 어긋날 대상 자체가 없으므로, 출처가 달라도 티가 나지
  않습니다.

  "국경선을 빼는" 방식으로는 안 됩니다. Natural Earth는 OSM 해안선보다
  한참 안쪽에서 끝나는 곳이 있어서(우크라이나는 그 면적이 약 42,000 km²),
  주 테두리가 국경선에서 수 km 떨어진 채 나란히 그려지고, 실제 주 경계를
  살릴 만큼 좁은 제거 반경으로는 그게 지워지지 않기 때문입니다. 반면 두
  주가 공유하는 변은 외곽선이 얼마나 어긋나든 정의상 항상 내부선입니다.

내륙 호수는 `countries-land`에서 폴리곤의 구멍으로 남는데, 그대로 두면
호수 둘레가 국경선처럼 그려지므로 스크립트에서 메웁니다.

### 맞닿은 나라끼리의 국경선

레바논과 이스라엘처럼 선택한 나라끼리 국경을 접하면 같은 국경이 양쪽
외곽선에 한 번씩, 총 두 번 그려집니다. 대부분 구간은 좌표가 정확히 같아
겹쳐 보이지만, 블루라인·셰바 농장 일대에서는 원본 데이터의 두 외곽선이
갈라져 사이에 빈 땅이 생기거나 서로 겹칩니다. 둘 다 같은 국경을 뜻하므로
스크립트가 한쪽 사본을 지웁니다(`dedupe_shared_borders`).

지우는 기준은 단순 근접이 아니라 **두 외곽선이 서로 다르게 주장하는 구역**
(빈 땅 + 겹침)의 테두리입니다. 단순히 "이웃 국경선에서 N km 이내"로 지우면
5km 어긋남을 잡을 만큼 넓힌 순간 레바논 해안선이 8km쯤 함께 지워집니다.
반면 빈 땅에 접한 두 선은 정의상 같은 국경이므로 안전합니다.

여기에 더해 그 구역을 **실제 육지로 마스킹**합니다. 두 나라 사이를 메우는
연산은 국경이 바다와 만나는 하구, 즉 양국 해안선이 수렴하는 지점의 바다도
함께 메우는데, 그 바닷조각 역시 양국 해안선에 둘러싸여 있어 기하학만으로는
빈 땅과 구별되지 않습니다. 분쟁 영토는 땅이지 바다가 아니므로 육지 마스크가
이를 갈라줍니다. 마스크는 국가 데이터와 같은 100m 해상도(`earth-lands-100m`)를
써야 해안선이 정확히 일치합니다 — 1km 해상도로는 최대 1km 어긋나 하구 부근
해안선이 2km가량 잘려 나갑니다.

이렇게 하면 잘리는 건 진짜 중복 국경뿐이라, 끊긴 자리는 이웃 나라의 선이
그대로 채웁니다. 열린 곡선을 억지로 다시 이어 붙일 필요가 없습니다.

어느 쪽 사본을 남길지는 ISO 코드 순으로 정하는데, 두 선의 스타일이 같아
결과에 차이가 없고 재현성만 있으면 되기 때문입니다.

### 나라 추가/변경하기

1. `scripts/build-borders.py`의 `TARGET`/`NAMES`를 수정하고
2. 스크립트 상단 주석의 안내대로 입력 데이터를 받아 실행하면 됩니다.

## 다음 단계 아이디어

- 원하는 지역만 담은 PMTiles를 직접 빌드해서 자체 호스팅으로 전환
- 다크 테마(`basemaps.namedFlavor("dark")`)나 커스텀 색상 팔레트 적용
- 국경선/주 경계에 hover 시 나라·주 이름 표시, 클릭 인터랙션 추가
- 3D 건물(`fill-extrusion`) 레이어로 입체감 있는 뷰 구성
