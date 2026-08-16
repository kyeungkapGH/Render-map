# Render Map

Leaflet과 OpenStreetMap을 사용한 웹 지도 시각화 프로젝트입니다.

## 시작하기

빌드 도구 없이 정적 파일만으로 동작합니다.

1. 저장소를 클론합니다.
2. `index.html`을 브라우저로 엽니다.
   - 또는 로컬 서버로 실행하려면:
     ```bash
     python3 -m http.server 8000
     ```
     이후 브라우저에서 `http://localhost:8000` 접속

## 구조

- `index.html` — 지도가 표시되는 페이지, Leaflet CDN을 불러옵니다.
- `map.js` — 지도 초기화, 타일 레이어, 마커 등 지도 로직.

## 배포

`claude/project-getting-started-5dwqgf` 브랜치에 푸시하면 `.github/workflows/deploy-pages.yml`
워크플로가 자동으로 GitHub Pages에 배포합니다.

최초 1회, 저장소 **Settings → Pages → Build and deployment → Source**를
`GitHub Actions`로 설정해야 워크플로가 실제로 페이지를 게시할 수 있습니다.

배포되면 다음 주소에서 확인할 수 있습니다:
`https://kyeungkapgh.github.io/Render-map/`

## 다음 단계 아이디어

- 마커를 데이터 파일(JSON/GeoJSON)에서 읽어와 여러 지점 표시
- 지역별 색상 구분(Choropleth) 레이어 추가
- 클릭/검색 등 상호작용 기능 추가
