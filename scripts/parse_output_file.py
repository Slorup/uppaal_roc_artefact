import os.path
import re

instance_to_ratio_dict: {str: float} = {
    "kim_cr": 33/10,
    "test_cr": 11,
    "surveil1": 3/4,
    "surveil2": 7/4,
    "surveil3": 7/2,
    "surveil4": 34/5,
    "complex_counter_example": 34/5
}

alg_to_plot_options_dict: {str: str} = {
    "mcr": "mark=*, mark options={solid}, color=red, loosely dashed, thick",
    "mcr_por": "mark=*, mark options={solid}, color=green, thick",
    "lambdadeduction": "mark=*, mark options={solid}, color=blue, dashed, thick"
}

def parse_result_data(result_folder):
    result_dict: dict[str, list[InstanceResult]] = {}
    alg_progress = 1

    for alg_name in os.listdir(result_folder):
        print(f"Parsing results for algorithm {alg_name} - {alg_progress}/{len(os.listdir(result_folder))}")
        result_dict[alg_name] = []
        for instance in os.listdir(f"{result_folder}/{alg_name}"):
            with open(f"{result_folder}/{alg_name}/{instance}", "r") as file:
                lines = file.readlines()
                ratios = []
                lp_count = 0
                lp_total_count = 0
                mcr_states = 0
                total_time = -1
                mcr_reduction_time = -1
                howards_time = -1
                por_time = -1
                memory = -1
                out_of_memory = False
                out_of_time = False
                uses_cost_reward = True
                instance_name = instance.split('.')[0]
                if instance_name in instance_to_ratio_dict:
                    optimal_ratio = instance_to_ratio_dict[instance_name]
                else:
                    optimal_ratio = None
                optimal_ratio_time = -1
                for line in lines:
                    res = re.match(r"Better ratio found after (\d+) linear", line)
                    if res:
                        lp_count = int(res.group(1))
                        lp_total_count += lp_count

                    res = re.match(r"No negative cycle found after solving (\d+) linear", line)
                    if res:
                        lp_total_count += int(res.group(1))

                    res = re.match(r"Found new better ratio: (\d*\.?\d+(?:[e][-+]\d+)?) \[Time: (\d+)", line)
                    if res:
                        ratio = float(res.group(1))
                        time = int(res.group(2))
                        if optimal_ratio is not None and abs(ratio - optimal_ratio) <= 0.0000001:
                            optimal_ratio_time = time
                        ratios.append((ratio, time, lp_count))

                    res = re.match(r"Found new better ratio: (\d+)/(\d+) \[Time: (\d+)", line)
                    if res:
                        ratio = float(res.group(1)) / float(res.group(2))
                        time = int(res.group(3))
                        if optimal_ratio is not None and abs(ratio - optimal_ratio) <= 0.0000001:
                            optimal_ratio_time = time
                        ratios.append((ratio, time, lp_count))

                    res = re.match("Total time: (\d+)ms", line)
                    if res:
                        total_time = int(res.group(1))

                    res = re.match("Out of memory", line)
                    if res:
                        out_of_memory = True

                    res = re.match("Timed Out", line)
                    if res:
                        out_of_time = True

                    res = re.match("glp_alloc: no memory available", line)
                    if res:
                        out_of_memory = True

                    res = re.match("Ratio type: Cost/Time", line)
                    if res:
                        uses_cost_reward = False

                    res = re.match(r"Number of states: (\d+)", line)
                    if res:
                        mcr_states = res.group(1)

                    res = re.match(r"Howard's - MCR solving time: (\d+)", line)
                    if res:
                        howards_time = res.group(1)

                    res = re.match(r"POR - Time spent on POR: (\d+)", line)
                    if res:
                        por_time = res.group(1)

                    res = re.match(r"MCR reduction time: (\d+)", line)
                    if res:
                        mcr_reduction_time = res.group(1)

                    res = re.match(r"@@@\d+.?\d+,(\d+)@@@", line)
                    if res:
                        memory = res.group(1)

                res = re.match(".*scaling(\d+)", instance)
                scaling_factor = -1
                if res:
                    scaling_factor = res.group(1)
                finished = not out_of_time and not out_of_memory
                res = InstanceResult(instance_name, ratios, int(optimal_ratio_time), int(total_time), int(scaling_factor), finished, out_of_memory, out_of_time, uses_cost_reward, int(mcr_states), int(howards_time), int(por_time), int(mcr_reduction_time), int(lp_total_count), int(memory))
                result_dict[alg_name].append(res)
        alg_progress += 1
    return result_dict


def latex_ratio_step_plots_all_instances(data):
    alg, instance_results = list(data.items())[0]
    for instance in instance_results:
        latex_ratio_step_plot(data, instance.instance_name)

def latex_ratio_step_plot(data, instance_name):
    latex_plot_legend = r"\legend{"
    for alg in data.keys():
        latex_plot_legend += f"{alg}, "
    latex_plot_legend +="}\n"

    latex_plot_data = ""
    for (alg, instance_results) in data.items():
        latex_plot_data += r"\addplot" + f"[const plot, {alg_to_plot_options_dict[alg]}] coordinates" + "{\n"

        instance_result = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
        for ratio, time, lp_count in instance_result.ratios:
            latex_plot_data += f"({time}, {ratio})\n"
        latex_plot_data += f"({instance_result.time_to_finish}, {instance_result.ratios[-1][0]}) %Finish time\n"
        latex_plot_data += r"};" + "\n"

    output_latex_content(f"{instance_name}_ratio_step_plot_data.txt", latex_plot_legend + latex_plot_data)

def latex_constant_scaling_plot(data, output_name):
    latex_plot_legend = r"\legend{"
    for alg in data.keys():
        latex_plot_legend += f"{alg}, "
    latex_plot_legend +="}\n"

    latex_plot_data = ""
    for (alg, instance_results) in data.items():
        latex_plot_data += r"\addplot" + f"[{alg_to_plot_options_dict[alg]}] coordinates" + "{\n"
        #Finds all instances that contains 'instance_name' in their name and has a scaling factor
        scaling_instances = [instance_result for instance_result in instance_results if instance_result.scaling_factor != -1]
        scaling_instances = sorted(scaling_instances, key=lambda x: x.scaling_factor)
        for scaling_instance in scaling_instances:
            #Still includes instances where they did not finish (time_to_finish = -1)
            latex_plot_data += f"({scaling_instance.scaling_factor}, {scaling_instance.time_to_finish})\n"
        latex_plot_data += r"};" + "\n"
    output_latex_content(f"{output_name}.txt", latex_plot_legend + latex_plot_data)

def output_latex_content(file_name, content):
    print(f"Writing to file: 'latex/{file_name}'")
    latex_file_table = open(os.path.join(os.getcwd(), f"latex/{file_name}"), "w")
    latex_file_table.write(content)

class InstanceResult:
    def __init__(self, instance_name, ratios, time_to_find_optimal, time_to_finish, scaling_factor, finished, out_of_memory, out_of_time, uses_cost_reward, mcr_states, howards_time, por_time, mcr_reduction_time, total_lp_count, memory):
        self.instance_name = instance_name
        self.ratios = ratios
        self.time_to_find_stored_optimal = time_to_find_optimal
        self.time_to_finish = time_to_finish
        self.scaling_factor = scaling_factor
        self.finished = finished
        self.out_of_memory = out_of_memory
        self.out_of_time = out_of_time
        self.uses_cost_reward = uses_cost_reward
        self.mcr_states = mcr_states
        self.howards_time = howards_time
        self.por_time = por_time
        self.mcr_reduction_time = mcr_reduction_time
        self.total_lp_count = total_lp_count
        self.memory = memory

def sort_results_data(results_data: dict[str, list[InstanceResult]]):
    for alg, instances in results_data.items():
        results_data[alg] = sorted(instances, key=lambda x: x.instance_name)

def prune_instances_not_on_all_algs(data: dict[str, list[InstanceResult]]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    common_instances = {}
    count = 0
    for alg, instances in data.items():
        if count == 0:
            common_instances = set(instances)
        else:
            common_instances.intersection(set(instances))
        count += 1

    common_instances_names = set(map(lambda x: x.instance_name, common_instances))

    for alg, instances in data.items():
        remaining_instances = [instance for instance in instances if instance.instance_name in common_instances_names]
        if len(remaining_instances) > 0:
            result_data[alg] = remaining_instances
    return result_data

def prune_instances_containing_str(data: dict[str, list[InstanceResult]], str: str) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    for alg, instances in data.items():
        remaining_instances = [instance for instance in instances if str not in instance.instance_name]
        if len(remaining_instances) > 0:
            result_data[alg] =remaining_instances
    return result_data

def filter_instances_to_contain_str(data: dict[str, list[InstanceResult]], str: str) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    for alg, instances in data.items():
        remaining_instances = [instance for instance in instances if str in instance.instance_name]
        if len(remaining_instances) > 0:
            result_data[alg] = remaining_instances
    return result_data

def latex_data_structure_size_plot(result_file):
    with open(result_file, "r") as file:
        latex_plot_legend = "\legend{waiting, parent}"
        latex_plot_data_waiting = "\\addplot[mark=*, mark options={solid}, color=red, loosely dashed, thick] coordinates{\n"
        latex_plot_data_passed = "\\addplot[mark=*, mark options={solid}, color=blue, dashed, thick] coordinates{\n"


        lines = file.readlines()
        for line in lines:
            res = re.match(r"Waiting size: (\d+) \[Time: (\d+)", line)
            if res:
                latex_plot_data_waiting += f"({res.group(2)}, {res.group(1)})\n"
            res = re.match(r"Parent size: (\d+) \[Time: (\d+)", line)
            if res:
                latex_plot_data_passed += f"({res.group(2)}, {res.group(1)})\n"

        latex_plot_data_waiting += "};\n"
        latex_plot_data_passed += "};\n"
        output_latex_content("data_structure_size_data.txt", latex_plot_legend + latex_plot_data_waiting + latex_plot_data_passed)

def latex_big_table(data: dict[str, list[InstanceResult]], prefix_until_N: str, output_name):
    alg_to_table_columns: {str: list[str]} = {
        "lambdadeduction": ["TotalTime", "Memory", "LpsSolved", "NumRatios", "BestRatio"],
        "mcr": ["TotalTime", "ReductionTime", "HowardTime", "Memory", "NumRatios", "BestRatio"],
        "mcr_por": ["TotalTime", "ReductionTime", "HowardTime", "PorTime", "Memory", "NumRatios", "BestRatio"]
    }
    column_to_table_name: {str: str} = {
        "TotalTime": "Time",
        "Memory": "Memory",
        "LpsSolved": "Lps",
        "NumRatios": "NumRatios",
        "BestRatio": "Ratio",
        "ReductionTime": "Reduc",
        "HowardTime": "Howard",
        "PorTime": "Por"
    }
    alg_to_table_name: {str: str} = {
        "lambdadeduction": "Symbolic $\lambda$\\nobreakdash-deduction",
        "mcr": "Concrete MCR",
        "mcr_por": "Concrete MCR + POR"
    }
    algs = []
    for (alg, instance_results) in data.items():
        if len(instance_results) > 0:
            algs.append(alg)

    latex_table = r"\begin{tabular}{c"
    for alg in algs:
        latex_table += "|"
        for column in alg_to_table_columns[alg]:
            latex_table += "c"
    latex_table += "}\n"

    for alg in algs:
        latex_table += "& \multicolumn{" + str(len(alg_to_table_columns[alg])) + "}{c}{" + alg_to_table_name[alg] + "} "
    latex_table += "\\\\\\hline\n"

    latex_table += "N"

    for alg in algs:
        for column in alg_to_table_columns[alg]:
            latex_table += " & " + column_to_table_name[column]
    latex_table += "\\\\\\hline\n"

    sort_results_data(data)

    instance_names = []
    for (alg, instance_results) in data.items():
        if alg not in algs:
            continue
        else:
            instance_names = [instance_result.instance_name for instance_result in instance_results]
            break

    for instance_name in instance_names:
        res = re.match(prefix_until_N + r"(\d+)", instance_name)
        if not res:
            continue
        latex_table += res.group(1)
        for (alg, instance_results) in data.items():
            if alg not in algs:
                continue
            instance_result: InstanceResult = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
            for column in alg_to_table_columns[alg]:
                latex_table += " & "
                match column:
                    case "TotalTime":
                        if instance_result.out_of_time:
                            latex_table += "OOT"
                        elif instance_result.time_to_finish >= 10000:
                            latex_table += f"{int(instance_result.time_to_finish / 1000)}s"
                        elif instance_result.time_to_finish != -1:
                            latex_table += f"{instance_result.time_to_finish}ms"
                        else:
                            latex_table += "N/A"
                    case "Memory":
                        if instance_result.out_of_memory:
                            latex_table += "OOM"
                        elif instance_result.memory != -1:
                            latex_table += f"{int(instance_result.memory/1024)}mb"
                        else:
                            latex_table += "N/A"
                    case "LpsSolved":
                        latex_table += f"{instance_result.total_lp_count}"
                    case "NumRatios":
                        latex_table += f"{len(instance_result.ratios)}"
                    case "BestRatio":
                        if len(instance_result.ratios) > 0:
                            latex_table += "%.4f" % instance_result.ratios[-1][0]
                        elif not instance_result.out_of_time and not instance_result.out_of_memory:
                            latex_table += "No sol."
                        else:
                            latex_table += "N/A"
                    case "ReductionTime":
                        if instance_result.mcr_reduction_time == -1:
                            latex_table += "N/A"
                        elif instance_result.mcr_reduction_time >= 10000:
                            latex_table += f"{int(instance_result.mcr_reduction_time / 1000)}s"
                        else:
                            latex_table += f"{instance_result.mcr_reduction_time}ms"
                    case "HowardTime":
                        if instance_result.howards_time == -1:
                            latex_table += "N/A"
                        elif instance_result.howards_time >= 10000:
                            latex_table += f"{int(instance_result.howards_time / 1000)}s"
                        else:
                            latex_table += f"{instance_result.howards_time}ms"
                    case "PorTime":
                        if instance_result.por_time == -1:
                            latex_table += "N/A"
                        elif instance_result.por_time >= 10000:
                            latex_table += f"{int(instance_result.por_time / 1000)}s"
                        else:
                            latex_table += f"{instance_result.por_time}ms"
        latex_table += "\\\\\\hline\n"
    latex_table += "\\end{tabular}"
    output_latex_content(f"{output_name}.txt", latex_table)

def filter_to_specific_algs(data: dict[str, list[InstanceResult]], algs: list[str]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}
    for alg, instances in data.items():
        if alg in algs:
            result_data[alg] = instances
    return result_data

os.chdir("../results")
result_data = parse_result_data(os.getcwd())
# result_data = prune_instances_not_on_all_algs(result_data)
# result_data = prune_instances_containing_str(result_data, "plus1")
result_data = filter_instances_to_contain_str(result_data, "job")
result_data = prune_instances_containing_str(result_data, "scaling")
result_data = filter_to_specific_algs(result_data, ["mcr", "lambdadeduction"])

os.chdir("../")
latex_dir = os.path.join(os.getcwd(), f"latex")
if not os.path.exists(latex_dir) or not os.path.isdir(latex_dir):
    os.mkdir(latex_dir)

latex_big_table(result_data, "job_m2_j", "big_table_job_data")
# latex_data_structure_size_plot(os.getcwd() + "/results/lambdadeduction/strandvejen_test_f2_v1_c1.txt")
# latex_constant_scaling_plot(result_data, "constant_scaling_plus1_plot_data")
#latex_ratio_step_plots_all_instances(result_data)
