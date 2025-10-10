import type * as Auth from "./type"
import { request } from "@/http/axios"

/** 登录并返回 Token */
export function loginApi(data: Auth.LoginRequestData) {
  return request<Auth.LoginResponseData>({
    url: "auth/login",
    method: "post",
    data
  })
}

/** 获取当前用户信息 */
export function getUserInfoApi() {
  return request<Auth.UserInfoResponseData>({
    url: "auth/me",
    method: "get"
  })
}
