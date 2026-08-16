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

라이브러리는 CDN 대신 `npm install`로 받아서 이 저장소 안에 직접 vendoring
했습니다. 버전을 올리려면 `npm install maplibre-gl@latest pmtiles@latest
@protomaps/basemaps@latest`로 받은 뒤 각 `dist/` 산출물을 `vendor/` 아래
같은 파일명으로 복사하면 됩니다.

## 타일 데이터에 대해

`map.js`의 `PMTILES_URL`은 Protomaps가 매일 새로 빌드해 공개하는 데모용
전세계 PMTiles 파일(`https://demo-bucket.protomaps.com/v4.pmtiles`)을
가리킵니다. 테스트/데모용으로만 의도된 것이라 트래픽이 많은 프로덕션에는
적합하지 않습니다.

실제 서비스로 쓰려면 직접 PMTiles 파일을 만들어 자체 호스팅(S3, R2, GitHub
Pages 등 Range 요청을 지원하는 정적 스토리지 어디든 가능)하는 것을
권장합니다:

- [maps.protomaps.com](https://maps.protomaps.com)에서 원하는 지역만
  추출한 PMTiles를 다운로드하거나
- [Planetiler](https://github.com/onthegomap/planetiler)로 직접 빌드한 뒤
- `map.js`의 `PMTILES_URL`만 해당 파일 주소로 바꾸면 됩니다.

## 배포

`claude/project-getting-started-5dwqgf` 브랜치에 푸시하면 `.github/workflows/deploy-pages.yml`
워크플로가 자동으로 GitHub Pages에 배포합니다.

최초 1회, 저장소 **Settings → Pages → Build and deployment → Source**를
`GitHub Actions`로 설정해야 워크플로가 실제로 페이지를 게시할 수 있습니다.

배포되면 다음 주소에서 확인할 수 있습니다:
`https://kyeungkapgh.github.io/Render-map/`

## 다음 단계 아이디어

- 원하는 지역만 담은 PMTiles를 직접 빌드해서 자체 호스팅으로 전환
- 다크 테마(`basemaps.namedFlavor("dark")`)나 커스텀 색상 팔레트 적용
- GeoJSON 오버레이 레이어, 클릭 인터랙션, 검색(geocoding) 추가
- 3D 건물(`fill-extrusion`) 레이어로 입체감 있는 뷰 구성
