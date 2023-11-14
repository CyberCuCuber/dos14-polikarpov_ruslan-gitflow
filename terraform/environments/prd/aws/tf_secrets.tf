variable "secrets" {
    description = "secrets to cloud conf"
    type = object ({
        authn = string
        bank = string
        authz = string
    })
    default = {
        authn = ""
        authz = "ggramal"
        bank = ""
    }
}