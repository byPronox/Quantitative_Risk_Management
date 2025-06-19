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

export async function createObservation(observation) {
  const response = await api.post("/observations/", observation);
  return response.data;
}

export async function fetchObservations(riskId) {
  const response = await api.get(`/observations/${riskId}`);
  return response.data;
}

export async function updateRiskStatus(riskId, status) {
  const response = await api.patch(`/risks/${riskId}/status`, status, {
    headers: { 'Content-Type': 'application/json' }
  });
  return response.data;
}
