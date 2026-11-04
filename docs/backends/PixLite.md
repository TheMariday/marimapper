# Advatek PixLite Mk3

Use a PixLite Mk3 controller that supports API v1.9. Configure the pixel
outputs in Advatek Assistant first. MariMapper subtracts leading null pixels
and counts each group as one logical LED, including any partial group at the
end of a string. LED 0 starts on the first output with logical LEDs. The count
continues in port order, skipping empty and all-null outputs.

The backend requests the first physical pixel in each group as its scan point.
The controller has accepted these addresses on an E16-S Mk3. Physical
verification for outputs with null pixels and grouping is pending.

Run these commands with your controller's address:

```sh
marimapper_check_backend pixlite --server <controller-address>
marimapper pixlite --server <controller-address>
```

The backend uses the controller's administrator account for test-data mode. For a password-protected
account, set the `PIXLITE_PASSWORD` environment variable and pass the full
HTTPS URL (PixLite uses port 4443). The controller certificate must be trusted.
Requests can use a CA bundle specified by `REQUESTS_CA_BUNDLE`.

Start with the controller in live mode. Scanning temporarily replaces live
output with the controller's test pattern and lights one pixel at a time.
Use this on a dedicated controller during the scan. The backend returns the
controller to live mode on exit. If the connection drops during cleanup or
the process is forcibly stopped, restore live mode in Advatek Assistant.
