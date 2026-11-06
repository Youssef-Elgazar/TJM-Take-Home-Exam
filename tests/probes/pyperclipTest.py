# pip install pyperclip
import time, pyperclip
from pywinauto import Desktop
from pywinauto.keyboard import send_keys

main = Desktop(backend="uia").window(title_re="^Fakturama - .*")
dlg = main.child_window(title="Select the address", control_type="Window")

search = dlg.child_window(control_type="Edit")
search.set_edit_text("Elgazar")
time.sleep(1)

# click the first data row (first-name column); coordinates are relative to the dialog
dlg.click_input(coords=(198, 97))
pyperclip.copy("")
send_keys("^c")
time.sleep(0.3)
print("clipboard:", repr(pyperclip.paste()))

search.set_edit_text("Northstar")   # should filter to nothing
time.sleep(1)
dlg.capture_as_image().save("dumps/search_northstar.png")
