#include "control/stm_serial.hpp"

#include <chrono>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <thread>

namespace {

struct Options {
    std::string port;
    int baud = 115200;
    double duration_s = 30.0;
    double period_s = 0.05;
    double vx_mps = 0.0;
    double vy_mps = 0.0;
    double wz_radps = 0.0;
    std::string output;
    std::string operator_id;
    std::string firmware_id;
    std::string safety_record;
    bool allow_actuation = false;
};

std::string Required(const std::map<std::string, std::string>& values, const std::string& name) {
    const auto found = values.find(name);
    if (found == values.end() || found->second.empty()) {
        throw std::invalid_argument("missing argument " + name);
    }
    return found->second;
}

Options Parse(int argc, char** argv) {
    std::map<std::string, std::string> values;
    bool allow = false;
    for (int index = 1; index < argc; ++index) {
        const std::string key = argv[index];
        if (key == "--allow-actuation") {
            allow = true;
            continue;
        }
        if (key == "--help" || key == "-h") {
            std::cout << "stm_probe --port PORT --output DIR --operator ID --firmware-id ID [--duration-s N] [--period-s N] [--baud N] [--vx N] [--vy N] [--wz N] [--allow-actuation --safety-record FILE]\n";
            std::exit(EXIT_SUCCESS);
        }
        if (index + 1 >= argc || key.rfind("--", 0U) != 0U) {
            throw std::invalid_argument("invalid command-line argument " + key);
        }
        values[key] = argv[++index];
    }
    Options options;
    options.port = Required(values, "--port");
    options.output = Required(values, "--output");
    options.operator_id = Required(values, "--operator");
    options.firmware_id = Required(values, "--firmware-id");
    options.baud = values.contains("--baud") ? std::stoi(values.at("--baud")) : options.baud;
    options.duration_s = values.contains("--duration-s") ? std::stod(values.at("--duration-s")) : options.duration_s;
    options.period_s = values.contains("--period-s") ? std::stod(values.at("--period-s")) : options.period_s;
    options.vx_mps = values.contains("--vx") ? std::stod(values.at("--vx")) : options.vx_mps;
    options.vy_mps = values.contains("--vy") ? std::stod(values.at("--vy")) : options.vy_mps;
    options.wz_radps = values.contains("--wz") ? std::stod(values.at("--wz")) : options.wz_radps;
    options.safety_record = values.contains("--safety-record") ? values.at("--safety-record") : "";
    options.allow_actuation = allow;
    if (options.baud <= 0 || options.duration_s <= 0.0 || options.period_s <= 0.0) {
        throw std::invalid_argument("baud, duration and period must be positive");
    }
    const bool moving = std::abs(options.vx_mps) > 0.0 || std::abs(options.vy_mps) > 0.0 || std::abs(options.wz_radps) > 0.0;
    if (moving && (!options.allow_actuation || options.safety_record.empty() || !std::filesystem::is_regular_file(options.safety_record))) {
        throw std::invalid_argument("motion requires --allow-actuation and an existing --safety-record");
    }
    return options;
}

std::uint64_t SystemNs() {
    return static_cast<std::uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count()
    );
}

void WriteEvent(std::ofstream& stream, std::uint64_t timestamp_ns, const std::string& type, const std::string& detail) {
    stream << timestamp_ns << ',' << type << ',' << detail << '\n';
}

}  // namespace

int main(int argc, char** argv) {
    cca::hardware::SerialPort serial;
    std::ofstream events;
    try {
        const auto options = Parse(argc, argv);
        const std::filesystem::path output(options.output);
        if (std::filesystem::exists(output) && !std::filesystem::is_empty(output)) {
            throw std::invalid_argument("output directory must be new or empty");
        }
        std::filesystem::create_directories(output);
        std::ofstream state(output / "robot_state.csv");
        std::ofstream control(output / "control.csv");
        events.open(output / "events.csv");
        if (!state || !control || !events) {
            throw std::runtime_error("unable to create capture CSV files");
        }
        state << "t_ns,x_m,y_m,theta_rad,vx_mps,vy_mps,omega_radps,flag_stop,voltage_v\n";
        control << "t_ns,vx_cmd_mps,vy_cmd_mps,wz_cmd_radps,vx_applied_mps,vy_applied_mps,wz_applied_radps\n";
        events << "t_ns,event_type,detail\n";
        serial.Open(options.port, options.baud);
        WriteEvent(events, SystemNs(), "serial_open", options.port);
        const cca::hardware::VelocityCommand requested{
            options.vx_mps, options.vy_mps, options.wz_radps, 0U, 0U
        };
        double x_m = 0.0;
        double y_m = 0.0;
        double theta_rad = 0.0;
        std::uint64_t last_state_ns = 0U;
        bool stop_latched = false;
        const auto start = std::chrono::steady_clock::now();
        const auto deadline = start + std::chrono::duration<double>(options.duration_s);
        while (std::chrono::steady_clock::now() < deadline) {
            const auto timestamp_ns = SystemNs();
            const auto command = stop_latched ? cca::hardware::VelocityCommand{} : requested;
            serial.SendVelocity(command);
            const auto telemetry = serial.ReadAvailable(timestamp_ns);
            if (telemetry.empty()) {
                WriteEvent(events, timestamp_ns, "telemetry_missing", "no_valid_frame");
            }
            for (const auto& sample : telemetry) {
                const double dt_s = last_state_ns == 0U ? 0.0 : static_cast<double>(sample.timestamp_ns - last_state_ns) * 1.0e-9;
                const double c = std::cos(theta_rad);
                const double s = std::sin(theta_rad);
                x_m += (c * sample.vx_mps - s * sample.vy_mps) * dt_s;
                y_m += (s * sample.vx_mps + c * sample.vy_mps) * dt_s;
                theta_rad = std::atan2(std::sin(theta_rad + sample.wz_radps * dt_s), std::cos(theta_rad + sample.wz_radps * dt_s));
                state << sample.timestamp_ns << ',' << x_m << ',' << y_m << ',' << theta_rad << ','
                      << sample.vx_mps << ',' << sample.vy_mps << ',' << sample.wz_radps << ','
                      << static_cast<unsigned int>(sample.flag_stop) << ',' << sample.voltage_v << '\n';
                control << sample.timestamp_ns << ',' << command.vx_mps << ',' << command.vy_mps << ',' << command.wz_radps << ','
                        << sample.vx_mps << ',' << sample.vy_mps << ',' << sample.wz_radps << '\n';
                last_state_ns = sample.timestamp_ns;
                if (sample.flag_stop != 0U) {
                    if (!stop_latched) {
                        WriteEvent(events, sample.timestamp_ns, "stm_stop_latched", "flag_stop_nonzero");
                    }
                    stop_latched = true;
                }
            }
            std::this_thread::sleep_for(std::chrono::duration<double>(options.period_s));
        }
        serial.SendZero();
        WriteEvent(events, SystemNs(), "zero_command", "normal_exit");
        serial.Close();
        const auto capture_time = SystemNs();
        std::ofstream capture(output / "capture.json");
        capture << "{\n"
                << "  \"schema\": \"cca-stm-cpp-capture-v1\",\n"
                << "  \"capture_source\": \"hardware\",\n"
                << "  \"transport\": \"stm32_serial\",\n"
                << "  \"ros\": false,\n"
                << "  \"bridge\": \"cpp\",\n"
                << "  \"operator\": \"" << options.operator_id << "\",\n"
                << "  \"firmware\": \"" << options.firmware_id << "\",\n"
                << "  \"captured_at_ns\": " << capture_time << ",\n"
                << "  \"geometry_authority\": \"pending_physical_measurement\",\n"
                << "  \"state_definition\": [\"x_m\", \"y_m\", \"theta_rad\", \"vx_mps\", \"vy_mps\", \"omega_radps\"]\n"
                << "}\n";
        std::ofstream manifest(output / "manifest.json");
        manifest << "{\n  \"schema\": \"cca-stm-cpp-candidate-v1\",\n  \"status\": \"CANDIDATE_NOT_EVIDENCE\",\n  \"capture\": \"capture.json\",\n  \"robot_state\": \"robot_state.csv\",\n  \"control\": \"control.csv\",\n  \"events\": \"events.csv\"\n}\n";
        return EXIT_SUCCESS;
    } catch (const std::exception& error) {
        serial.SendZero();
        if (events) {
            WriteEvent(events, SystemNs(), "error", error.what());
        }
        std::cerr << error.what() << '\n';
        return EXIT_FAILURE;
    }
}
