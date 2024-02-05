# Kassal.app Home Assistant integration

--------

[![GitHub Release][releases-shield]][releases]
[![Downloads][download-latest-shield]](Downloads)
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]
[![hacs][hacsbadge]][hacs]


![Kassalapp][logo]

_Integration to integrate with [kassal.app][kassalapp]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`todo` | One entity is created for each of your kassal.app shoppings lists.


## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=bendikrb&repository=ha-kassalapp&category=Integration)

Or
Search for `Kassalapp` in HACS and install it under the "Integrations" category.

### Manual Installation
<details>
<summary>More Details</summary>

* You should take the latest [published release](https://github.com/bendikrb/ha-kassalapp/releases).  
* To install, place the contents of `custom_components` into the `<config directory>/custom_components` folder of your Home Assistant installation.
* Restart Home Assistant
* In the HA UI go to Settings -> Integrations click "+" and search for "Kassalapp"
</details>

## Configuration is done in the UI

The configuration UI will guide you through adding the integration to Home Assistant, you just need an account at [kassal.app](https://kassal.app) with a valid API token. 

***
[kassalapp]: https://kassal.app
[commits-shield]: https://img.shields.io/github/commit-activity/y/bendikrb/ha-kassalapp.svg?style=for-the-badge
[commits]: https://github.com/bendikrb/ha-kassalapp/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge
[logo]: docs/assets/logo.png
[icon]: docs/assets/icon.png
[license-shield]: https://img.shields.io/github/license/bendikrb/ha-kassalapp.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40bendikrb-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/bendikrb/ha-kassalapp.svg?style=for-the-badge
[releases]: https://github.com/bendikrb/ha-kassalapp/releases
[download-latest-shield]: https://img.shields.io/github/downloads/bendikrb/ha-kassalapp/latest/total?style=for-the-badge
