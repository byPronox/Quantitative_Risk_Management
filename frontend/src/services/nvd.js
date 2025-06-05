import api from "./api";

export async function fetchNvdVulnerabilities(keyword = "react") {
  const response = await api.get("/nvd", {
    params: { keyword }
  });
  return response.data;
}
