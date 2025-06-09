import api from "./api";

export async function fetchNvdVulnerabilities(keyword = "react") {
  const response = await api.get("/nvd", {
    params: { keyword }
  });
  return response.data;
}

export async function analyzeNvdRisk() {
  const response = await api.post("/nvd/analyze_risk");
  return response.data;
}

export async function addKeywordToQueue(keyword) {
  const response = await api.post("/nvd/add_to_queue", {
    keyword: keyword
  });
  return response.data;
}
