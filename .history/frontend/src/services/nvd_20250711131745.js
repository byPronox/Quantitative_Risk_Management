import api from "./api";

export async function fetchNvdVulnerabilities(keyword = "apache") {
  // Use Kong proxy to NVD API directly
  const response = await api.get("/nvd/cves/2.0", {
    params: { keywordSearch: keyword }
  });
  return response.data;
}

export async function analyzeNvdRisk() {
  const response = await api.post("/nvd/analyze_risk");
  return response.data;
}

export async function addKeywordToQueue(keyword) {
  const response = await api.post("/nvd/queue/add", {
    keyword: keyword
  });
  return response.data;
}
