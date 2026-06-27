Set shell = CreateObject("WScript.Shell")
scriptPath = WScript.ScriptFullName
scriptDir = Left(scriptPath, InStrRev(scriptPath, "\"))
windowStyle = 0

shell.CurrentDirectory = scriptDir
shell.Environment("PROCESS")("PYTHONPATH") = scriptDir & "src"

pythonExe = "pythonw.exe"
If FindOnPath("pythonw.exe") = "" Then
    pythonExe = "python.exe"
End If

arguments = ""
For Each argument In WScript.Arguments
    arguments = arguments & " " & Quote(argument)
Next

command = Quote(pythonExe) & " -m biscuit" & arguments
shell.Run command, windowStyle, False

Function Quote(value)
    Quote = """" & Replace(value, """", """""") & """"
End Function

Function FindOnPath(fileName)
    paths = Split(shell.Environment("PROCESS")("PATH"), ";")
    For Each path In paths
        candidate = path
        If Len(candidate) > 0 Then
            If Right(candidate, 1) <> "\" Then
                candidate = candidate & "\"
            End If
            candidate = candidate & fileName
            If CreateObject("Scripting.FileSystemObject").FileExists(candidate) Then
                FindOnPath = candidate
                Exit Function
            End If
        End If
    Next
    FindOnPath = ""
End Function
