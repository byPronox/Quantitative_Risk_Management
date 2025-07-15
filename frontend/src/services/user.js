import api from "./api";

export const loginUser = async (username, password) => {
  const response = await api.post("/user/login", { username, password });
  return response.data;
};

export const getUserProfile = async (token) => {
  const response = await api.get(`/user/profile`, { params: { token } });
  return response.data;
};
