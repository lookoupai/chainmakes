export type CurrentUserResponseData = ApiResponseData<{
  id: number
  username: string
  email: string | null
  roles: string[]
}>

export interface UpdateUserRequest {
  email?: string
  password?: string
}
