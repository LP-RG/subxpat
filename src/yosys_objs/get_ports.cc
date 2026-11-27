
#include "kernel/yosys.h"

USING_YOSYS_NAMESPACE
PRIVATE_NAMESPACE_BEGIN

struct GetPortsPass : public Pass {
	GetPortsPass()
	    : Pass("get_ports", "Print module ports in declaration order") {}

	void execute(std::vector<std::string> args, RTLIL::Design *design) override {
		log_header(design, "Printing module ports\n");

		for (auto module : design->selected_modules()) {
			log("-- START PORTS DATA --\n");

			for (auto port_name : module->ports) {
				RTLIL::Wire *wire = module->wire(port_name);
				if (wire == nullptr) continue;

				char const *direction = "";
				if (wire->port_input) direction = "input";
				else if (wire->port_output) direction = "output";
				else continue;

				log("%s %s %d\n", direction, log_id(port_name), wire->width);
			}

			log("-- END PORTS DATA --");
		}
	}
} GetPortsPass;

PRIVATE_NAMESPACE_END
