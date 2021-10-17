#!/usr/bin/env python3

import argparse
import os
from litex.build.io import CRG
from litex.build.generic_platform import Subsignal, Pins
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.builder import Builder

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),

        Subsignal("sink_valid",   Pins(1)),
        Subsignal("sink_ready",   Pins(1)),
        Subsignal("sink_data",    Pins(8)),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

# Simulation SoC -----------------------------------------------------------------------------------

class SimSoC(SoCCore):
    def __init__(self, sim_debug = False, trace_reset_on = False, cpu_type="vexriscv"):

        platform     = Platform()
        sys_clk_freq = int(1e6)
        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            ident         = "LiteX Simulation",
            ident_version = True,
            uart_name     = "sim",
            integrated_rom_size=0x20000,
            cpu_type=cpu_type)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # Simulation debugging ----------------------------------------------------------------------
        if sim_debug:
            platform.add_debug(self, reset=1 if trace_reset_on else 0)
        else:
            self.comb += platform.trace.eq(1)

# Build --------------------------------------------------------------------------------------------

def generate_gtkw_savefile(builder, vns, trace_fst):
    from litex.build.sim import gtkwave as gtkw
    dumpfile = os.path.join(builder.gateware_dir, "sim.{}".format("fst" if trace_fst else "vcd"))
    savefile = os.path.join(builder.gateware_dir, "sim.gtkw")
    soc = builder.soc

    with gtkw.GTKWSave(vns, savefile=savefile, dumpfile=dumpfile) as save:
        save.clocks()
        save.fsm_states(soc)
        if "main_ram" in soc.bus.slaves.keys():
            save.add(soc.bus.slaves["main_ram"], mappers=[gtkw.wishbone_sorter(), gtkw.wishbone_colorer()])

        if hasattr(soc, "sdrphy"):
            # all dfi signals
            save.add(soc.sdrphy.dfi, mappers=[gtkw.dfi_sorter(), gtkw.dfi_in_phase_colorer()])

            # each phase in separate group
            with save.gtkw.group("dfi phaseX", closed=True):
                for i, phase in enumerate(soc.sdrphy.dfi.phases):
                    save.add(phase, group_name="dfi p{}".format(i), mappers=[
                        gtkw.dfi_sorter(phases=False),
                        gtkw.dfi_in_phase_colorer(),
                    ])

            # only dfi command/data signals
            def dfi_group(name, suffixes):
                save.add(soc.sdrphy.dfi, group_name=name, mappers=[
                    gtkw.regex_filter(gtkw.suffixes2re(suffixes)),
                    gtkw.dfi_sorter(),
                    gtkw.dfi_per_phase_colorer(),
                ])

            dfi_group("dfi commands", ["cas_n", "ras_n", "we_n"])
            dfi_group("dfi commands", ["wrdata"])
            dfi_group("dfi commands", ["wrdata_mask"])
            dfi_group("dfi commands", ["rddata"])

def sim_args(parser):
    parser.add_argument("--trace",                action="store_true",     help="Enable Tracing")
    parser.add_argument("--trace-fst",            action="store_true",     help="Enable FST tracing (default=VCD)")
    parser.add_argument("--trace-start",          default="0",             help="Time to start tracing (ps)")
    parser.add_argument("--trace-end",            default="-1",            help="Time to end tracing (ps)")
    parser.add_argument("--opt-level",            default="O3",            help="Compilation optimization level")
    parser.add_argument("--sim-debug",            action="store_true",     help="Add simulation debugging modules")
    parser.add_argument("--gtkwave-savefile",     action="store_true",     help="Generate GTKWave savefile")

def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    sim_args(parser)
    args = parser.parse_args()

    # Configuration --------------------------------------------------------------------------------
    sys_clk_freq = int(1e6)
    sim_config = SimConfig()
    sim_config.add_clocker("sys_clk", freq_hz=sys_clk_freq)
    sim_config.add_module("serial2console", "serial")

    trace_start = int(float(args.trace_start))
    trace_end = int(float(args.trace_end))

    # SoC ------------------------------------------------------------------------------------------
    soc = SimSoC()

    # Build/Run ------------------------------------------------------------------------------------
    def pre_run_callback(vns):
        if args.trace:
            generate_gtkw_savefile(builder, vns, args.trace_fst)

    builder = Builder(soc)
    builder.build(
        sim_config       = sim_config,
        opt_level        = args.opt_level,
        trace            = args.trace,
        trace_fst        = args.trace_fst,
        trace_start      = trace_start,
        trace_end        = trace_end,
        pre_run_callback = pre_run_callback
    )

if __name__ == "__main__":
    main()