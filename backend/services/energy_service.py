from __future__ import annotations
import datetime
import math
import numpy as np
import pytz
import pysolar
pysolar.use_math()
from pysolar.solar import get_altitude
from pysolar.radiation import get_radiation_direct
from ..repositories.constants import Constants


class EnergyService:
    """Energy calculations: kWp→kWh, tilt factor, monthly irradiation."""

    def __init__(self, timezone: str = Constants.DEFAULT_TZ):
        self.tz = timezone

    def tilt_factor(
        self, tilt_angle_deg: float,
        latitude: float, longitude: float,
        reference_date: str = "2021/09/21 12:10:00",
    ) -> float:
        local_dt = datetime.datetime.strptime(reference_date, "%Y/%m/%d %H:%M:%S")
        utc_dt = local_dt.astimezone(pytz.utc)
        solar_alt = get_altitude(latitude, longitude, utc_dt)
        solar_zenith = 90 - solar_alt
        return self._transposition_factor(tilt_angle_deg, solar_zenith)

    @staticmethod
    def _transposition_factor(beta_deg: float, Z_ref_deg: float) -> float:
        beta = math.radians(beta_deg)
        Z_ref = math.radians(Z_ref_deg)
        return (math.cos(beta) * math.cos(Z_ref) + math.sin(beta) * math.sin(Z_ref)) / math.cos(Z_ref)

    @staticmethod
    def annual_kWh(
        total_kWp: float,
        pvout_kWh_per_kWp: float,
        tilt_factor: float,
        pvsyst_ratio: float = Constants.PVSYST_RATIO,
    ) -> float:
        return total_kWp * pvout_kWh_per_kWp * pvsyst_ratio * tilt_factor

    def get_daily_irradiation(
        self, year: int, month: int, day: int,
        latitude: float, longitude: float,
    ) -> float:
        tz_info = pytz.timezone(self.tz)
        date = datetime.datetime(year, month, day, 12, 0, 0, tzinfo=tz_info)
        alt_deg = get_altitude(latitude, longitude, date)
        if alt_deg <= 0:
            return 0.0
        return float(get_radiation_direct(date, alt_deg))

    def get_monthly_percent(
        self, year: int, latitude: float, longitude: float,
    ) -> list[float]:
        monthly = []
        for month in range(1, 13):
            daily_vals = []
            for day in range(1, 32):
                try:
                    val = self.get_daily_irradiation(year, month, day, latitude, longitude)
                    daily_vals.append(val)
                except (ValueError, OverflowError):
                    continue
            monthly.append(float(np.mean(daily_vals)) if daily_vals else 0.0)

        total = sum(monthly)
        if total <= 0:
            return list(Constants.MONTHLY_PERCENT_DEFAULT)
        return [(x / total) * 100 for x in monthly]
