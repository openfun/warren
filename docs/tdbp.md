# Warren-TdBP

France Université Numérique presents an educational dashboard solution to give you more
visibility over your Moodle courses.

This solution, integrated with `Warren`, is based on:

- The [`warren-tdbp`](https://github.com/apui-avignon-university/warren-tdbp)
  Warren plugin, developed by FUN and maintained by APUI Avignon Université.
- the
  [`moodle-logstore_xapi`](https://github.com/apui-avignon-university/moodle-logstore_xapi)
  Moodle plugin, developed by APUI Avignon Université. Note that Moodle 3.9+ is required.

## Setting up xAPI statements

To start, install the
[`moodle-logstore_xapi`](https://github.com/apui-avignon-university/moodle-logstore_xapi)
plugin on your Moodle instance. Refer to the [Moodle
documentation](https://docs.moodle.org/404/en/Installing_plugins) for installation
instructions.

### Configuring the plugin

Navigate to `Site administration` > `Logging` > `Logstore xAPI` and configure the plugin
as follows:

- `endpoint`: `https://ralph.tdbp.fun-data.fr/xAPI/statements`
- `username` and `password`: **provided by FUN**
- `resendfailedbatches`: `True`
- `shortcourseid`: `True`
- `sendidnumber`: `True`
- `send_username`: `True`
- `sendresponsechoices`: `True`
- `enablesendingnotifications`: `False`

Leave all other entries at their defaults.

Once configured, the plugin will periodically send xAPI statements to the FUN Ralph
instance.

## Configuring Moodle Web Services

Warren-TdBP (specifically the Experience Index) requires knowledge of your course
architecture (course and activity/resource identifiers and relations) to
provide an educational dashboard. Therefore, you need to setup two Moodle webservices.

### Configuring the web services

Navigate to `Site administration` > `Server` > `Web services` > `Overview`.
Follow the 10 steps provided by Moodle:

1. Enable web service: `Yes`
2. Enable protocols: `rest`
3. Create a specific user: `warren_tdbp`
4. Check its user capability
5. Select a service: add a new service (let's name it `Warren-TdBP - XI`)
6. Add functions: new service `Warren-TdBP - XI` needs to have the following functions:
   - `core_course_get_courses` to get course details.
   - `core_course_get_contents` to get course contents.
7. Select a specific user: select the user previously created `warren_tdbp`
8. Create a token for a user: create a token for user `warren_tdbp`

## Configuring Warren-TdBP as an External Tool

Next, configure Warren-TdBP as an external tool in your Moodle instance.

### Configuring the external tool

Navigate to `Site administration` > `External tool` > `Manage tools` and add a manual
configuration for a new tool with the following settings:

- Tool name: `Warren-TdBP`
- Tool URL: `https://warren.preprod-tdbp.apps.openfun.fr`
- LTI version: `LTI 1.0/1.1`
- Consumer key and shared secret: **given by FUN**
- Default launch container: `New window`
- Supports Deep linking: `Enabled`
- Content Selection URL: `https://warren.preprod-tdbp.apps.openfun.fr/lti/select`
- Share launcher's name with tool: `Always`
- Share launcher's email with tool: `Always`
- Tool configuration usage: `Show as preconfigured tool when adding an external tool`
- Default launch container: `Existing window`

Leave all other entries at their defaults.

## Adding Warren-TdBP in a course

Finally, add Warren-TdBP as a new activity in the course of your choice by following
these steps:

1. Navigate to the desired course
2. Switch to **Edit Mode** and select **Add a new activity**
3. Choose the preconfigured `Warren-TdBP` external tool
4. On the `Add external tool page`, click **Select content**.
5. In the window that opens, select `tdbp`
6. Click **Save and View** to access the education dashboard
