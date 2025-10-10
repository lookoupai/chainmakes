export interface LoginRequestData {
  /** 用户名 */
  username: string
  /** 密码 */
  password: string
}

export interface LoginResponseData {
  access_token: string
  token_type: string
}

export interface UserInfo {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

export type UserInfoResponseData = ApiResponseData<UserInfo>
