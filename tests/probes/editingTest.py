import time
from pywinauto import Desktop

main = Desktop(backend="uia").window(title_re="^Fakturama - .*")
save = main.child_window(title="Save the current contents", control_type="Button")
ref = main.child_window(title="Cust.Ref.", control_type="Edit")

print("save enabled before:", save.is_enabled())

ref.set_edit_text("TEST-SETTEXT")
time.sleep(0.5)
print("after set_edit_text -> value:", ref.get_value(), "| save enabled:", save.is_enabled())

ref.set_edit_text("")
ref.set_focus()
ref.type_keys("TEST-KEYS", with_spaces=True)
time.sleep(0.5)
print("after type_keys -> value:", ref.get_value(), "| save enabled:", save.is_enabled())
