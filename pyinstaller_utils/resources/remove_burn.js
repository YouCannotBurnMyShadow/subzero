
// we may have a problem with escaped quotes
var oReg = new ActiveXObject('winmgmts:{impersonationLevel=impersonate}!\\.\root\default:StdRegProv')

oReg.EnumKey(hDefKey, strKeyPath, arrSubKeys)


for(strSubkey in arrSubKeys) {
  strSubKeyPath = strKeyPath + '\\' + strSubkey
  oReg.EnumValues(hDefKey, strSubKeyPath, arrValueNames, arrTypes)
    for(strValueName in arrValueNames) {
        switch(arrTypes[i]) {
          case REG_SZ:
            oReg.GetStringValue hDefKey, strSubKeyPath, strValueName, strValue
        }
    }
}