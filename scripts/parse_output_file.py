import os.path
import re
from collections import OrderedDict

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
    "concretemcr": "color=blue, loosely dashed, thick",
    "concretemcr_por": "color=green, thick",
    "lambdadeduction": "color=red, dashed, thick",
    "lambdadeduction_no_optimisations": "color=blue, loosely dashed, thick",
    "lambdadeduction_prune_parent": "color=gray, densely dotted, thick",
    "lambdadeduction_reuse_waiting": "color=green, dotted, thick",
    "lambdadeduction_transformation_matrix": "color=black, dash dot, thick",
    "lambdadeduction_full_reset_cost": "color=magenta, thick",
    "lambdadeduction_keep_parent": "color=magenta, thick",
    "lambdadeduction_full_no_reuse_waiting": "color=magenta, thick"
}

alg_to_table_name: {str: str} = {
    "lambdadeduction": "S-$\lambda$D - All opt.",
    "lambdadeduction_no_optimisations": "S-$\lambda$D - No opt.",
    "lambdadeduction_prune_parent": "S-$\lambda$D - Parent Pruning",
    "lambdadeduction_reuse_waiting": "S-$\lambda$D - Reuse Waiting",
    "lambdadeduction_transformation_matrix": "S-$\lambda$D - Matrices",
    # "lambdadeduction_full_reset_cost": "Symbolic $\lambda$\\nobreakdash-deduction - All opt. + cost reset",
    # "lambdadeduction_keep_parent": "Symbolic $\lambda$\\nobreakdash-deduction - All opt. + Keep parent",
    "lambdadeduction_full_no_reuse_waiting": "S-$\lambda$D - Matrices + Parent Pruning",
    "concretemcr": "CP-MCR",
    "concretemcr_por": "CP-MCR + POR"
}

class InstanceResult:
    def __init__(self, instance_name, ratios, time_to_find_optimal, time_to_finish, scaling_factor, finished, out_of_memory, out_of_time, uses_cost_reward, mcr_states, howards_time, por_time, mcr_reduction_time, total_lp_count, memory_script, time_script, clean_waiting, no_transformation_matrix, number_of_mcr_location_vectors):
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
        self.memory_script = memory_script
        self.time_script = time_script
        self.clean_waiting = clean_waiting
        self.no_transformation_matrix = no_transformation_matrix
        self.number_of_mcr_location_vectors = number_of_mcr_location_vectors

    def get_value(self, category_str):
        match category_str:
            case "Time":
                return self.time_to_finish / 1000 if self.time_to_finish != -1 else -1
            case "Memory":
                return self.memory_script / 1000 if self.memory_script != -1 else -1

def parse_result_data(result_folder, time_limit_seconds, memory_limit_mb):
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
                memory_script = -1
                time_script = -1
                number_of_mcr_location_vectors = -1
                out_of_memory = False
                out_of_time = False
                uses_cost_reward = True
                clean_waiting_list = False
                no_transformation_matrix = False
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

                    res = re.match("glp_alloc: no memory available", line)
                    if res:
                        out_of_memory = True

                    res = re.match("Command terminated by signal 11", line)
                    if res:
                        out_of_memory = True

                    res = re.match("Command terminated by signal 6", line)
                    if res:
                        out_of_memory = True

                    res = re.match("Timed Out", line)
                    if res:
                        out_of_time = True

                    res = re.match(r"@@@(\d+).?(\d+),(\d+)@@@", line)
                    if res:
                        t = float(res.group(1)) + float(f"0.{res.group(2)}")
                        m = int(res.group(3))
                        time_script = t
                        memory_script = m
                        if t >= time_limit_seconds:
                            out_of_time = True
                        if m/1000 >= memory_limit_mb:
                            out_of_memory = True

                    res = re.match("Ratio type: Cost/Time", line)
                    if res:
                        uses_cost_reward = False

                    res = re.match(r"Number of states: (\d+)", line)
                    if res:
                        mcr_states = res.group(1)

                    res = re.match(r"Number of unique location vectors: (\d+)", line)
                    if res:
                        number_of_mcr_location_vectors = res.group(1)

                    res = re.match(r"Clean waiting list each iteration: (\d)", line)
                    if res:
                        clean_waiting_list = res.group(1) == "1"

                    res = re.match(r"No transformation matrix usage: (\d)", line)
                    if res:
                        no_transformation_matrix = res.group(1) == "1"

                    res = re.match(r"Howard's - MCR solving time: (\d+)", line)
                    if res:
                        howards_time = res.group(1)

                    res = re.match(r"POR - Time spent on POR: (\d+)", line)
                    if res:
                        por_time = res.group(1)

                    res = re.match(r"MCR reduction time: (\d+)", line)
                    if res:
                        mcr_reduction_time = res.group(1)

                res = re.match(".*scaling(\d+)", instance)
                scaling_factor = -1
                if res:
                    scaling_factor = int(res.group(1))
                finished = not out_of_time and not out_of_memory
                res = InstanceResult(instance_name, ratios, int(optimal_ratio_time), int(total_time), int(scaling_factor), finished, out_of_memory, out_of_time, uses_cost_reward, int(mcr_states), int(howards_time), int(por_time), int(mcr_reduction_time), int(lp_total_count), int(memory_script), int(time_script), clean_waiting_list, no_transformation_matrix, int(number_of_mcr_location_vectors))
                result_dict[alg_name].append(res)
        alg_progress += 1
    return result_dict


def latex_ratio_step_plots_all_instances(data: dict[str, list[InstanceResult]], alg):
    instance_results = data[alg]
    latex_plot_data = ""
    did_not_finish_value = 1800
    for instance in instance_results:
        latex_plot_data += r"\addplot" + "[const plot, mark=square] coordinates{ %" + instance.instance_name + "\n"
        last_ratio = 10000
        last_time = 0
        for ratio,time,lp_count in instance.ratios:
            latex_plot_data += f"({time / 1000}, {ratio})\n"
            last_ratio = ratio
            last_time = time / 1000
        latex_plot_data += "};\n"
        if instance.finished:
            latex_plot_data += r"\addplot" + "[const plot, mark=square*] coordinates{ %" + instance.instance_name + " last point\n"
            latex_plot_data += f"({instance.time_to_finish / 1000}, {last_ratio}) %Finish time\n"
            latex_plot_data += "};\n"
            latex_plot_data += r"\addplot" + "[const plot] coordinates{ %" + instance.instance_name + " last line\n"
            latex_plot_data += f"({last_time}, {last_ratio}) %Latest ratio point\n"
            latex_plot_data += f"({instance.time_to_finish / 1000}, {last_ratio}) %Finish time\n"
            latex_plot_data += "};\n"
        else:
            latex_plot_data += r"\addplot" + "[const plot] coordinates{ %" + instance.instance_name + " last line\n"
            latex_plot_data += f"({last_time}, {last_ratio}) %Latest ratio point\n"
            latex_plot_data += f"({did_not_finish_value}, {last_ratio}) %Did not finish\n"
            latex_plot_data += "};\n"
    output_latex_content("strandvejen_step_plot.txt", latex_plot_data)

def latex_ratio_step_plot(data: dict[str, list[InstanceResult]], instance_name):
    latex_plot_legend = r"\legend{"
    for alg in data.keys():
        latex_plot_legend += f"{alg}, "
    latex_plot_legend +="}\n"

    latex_plot_data = ""
    for (alg, instance_results) in data.items():
        latex_plot_data += r"\addplot" + "[const plot, mark=*, mark options={solid}, " + f"{alg_to_plot_options_dict[alg]}] coordinates" + "{\n"

        instance_result = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
        for ratio, time, lp_count in instance_result.ratios:
            latex_plot_data += f"({time}, {ratio})\n"
        latex_plot_data += f"({instance_result.time_to_finish}, {instance_result.ratios[-1][0]}) %Finish time\n"
        latex_plot_data += r"};" + "\n"

    output_latex_content(f"{instance_name}_ratio_step_plot_data.txt", latex_plot_legend + latex_plot_data)

def latex_constant_scaling_plot(data: dict[str, list[InstanceResult]], output_name, alg_name):
    instance_type_to_mark_options = {
        "strandvejen": "mark=square, color=red",
        "surveil": "mark=o, color=dgreen",
        "job": "mark=triangle, color=blue"
    }

    instance_type_to_points: dict[str, list[str]] = {}

    data = prune_instances_not_on_all_algs(data, False)
    sort_results_data(data)

    instance_names: list[str] = []
    for (alg, instance_results) in data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        break

    did_not_finish_value = 5000
    min_value = 0.001
    latex_legend_data = "\\legend{"
    latex_plot_data = ""

    for (alg, instance_results) in data.items():
        if alg != alg_name:
            continue
        prev_name = ""
        for instance_result in instance_results:
            res = re.match(r"(.*)_scaling", instance_result.instance_name)
            if not res:
                continue

            if res.group(1) != prev_name:
                prev_name = res.group(1)
                instances_of_this_type = [instance_result for instance_result in instance_results if prev_name in instance_result.instance_name]
                instance_type_name = instance_result.instance_name.split("_")[0]
                if instance_type_name == "job":
                    latex_legend_data += f"Job,"
                elif instance_type_name == "strandvejen":
                    latex_legend_data += "Strandvejen,"
                elif instance_type_name == "surveil":
                    latex_legend_data += "Surveil,"
                else:
                    latex_legend_data += "Unknown,"
                latex_plot_data += "\\addplot[" + instance_type_to_mark_options[instance_type_name] + ", thick] coordinates{ %" + prev_name + "\n"

                for specific_instance in sorted(instances_of_this_type, key=lambda x: x.scaling_factor):
                    res = re.match(r".*scaling(\d+)", specific_instance.instance_name)
                    if not res:
                        continue
                    scaling = int(res.group(1))
                    if specific_instance.finished:
                        time = specific_instance.get_value("Time")
                        latex_plot_data += f"({scaling}, {time if time > min_value else min_value})\n"
                    else:
                        latex_plot_data += f"({scaling}, {did_not_finish_value})\n"
                latex_plot_data += "};\n"
    latex_legend_data += "}"
    output_latex_content(output_name + ".txt", latex_legend_data + "\n" + latex_plot_data)

def latex_state_scaling_plot(data: dict[str, list[InstanceResult]]):
    instance_type_to_mark_options = {
        "strandvejen": "mark=square, color=red",
        "surveil": "mark=o, color=dgreen",
        "job": "mark=triangle, color=blue"
    }

    algs = ["concretemcr", "lambdadeduction_full_no_reuse_waiting"]
    res_data = filter_to_specific_algs(data, algs)
    res_data = prune_instances_not_on_all_algs(res_data, False)
    sort_results_data(res_data)
    mcr_instances = res_data["concretemcr"]

    instance_name_to_average_discrete_states = {}

    for count in range(0, len(mcr_instances)):
        mcr_instance = mcr_instances[count]
        mcr_states = mcr_instance.mcr_states
        mcr_num_loc_vectors = mcr_instance.number_of_mcr_location_vectors
        if mcr_states == 0 or mcr_num_loc_vectors == -1:
            continue
        instance_name_to_average_discrete_states[mcr_instance.instance_name] = int(mcr_states) / int(mcr_num_loc_vectors)

    min_value = 0.001
    did_not_finish_value = 5000
    for (alg, instance_results) in res_data.items():
        latex_legend_data = "\\legend{"
        latex_plot_data = ""
        prev_name = ""
        for instance_result in sorted(instance_results, key=lambda x: x.instance_name):
            res = re.match(r"(.*)_scaling", instance_result.instance_name)
            if not res:
                continue

            if res.group(1) != prev_name:
                prev_name = res.group(1)
                instances_of_this_type = [instance_result for instance_result in instance_results if prev_name in instance_result.instance_name and instance_result.instance_name in instance_name_to_average_discrete_states.keys()]
                instance_type_name = instance_result.instance_name.split("_")[0]
                if instance_type_name == "job":
                    latex_legend_data += f"Job,"
                elif instance_type_name == "strandvejen":
                    latex_legend_data += "Strandvejen,"
                elif instance_type_name == "surveil":
                    latex_legend_data += "Surveil,"
                else:
                    latex_legend_data += "Unknown,"
                latex_plot_data += "\\addplot[" + instance_type_to_mark_options[instance_type_name] + ", thick] coordinates{ %" + prev_name + "\n"

                for specific_instance in sorted(instances_of_this_type, key=lambda x: instance_name_to_average_discrete_states[x.instance_name]):
                    average_discrete_states = instance_name_to_average_discrete_states[specific_instance.instance_name]
                    if specific_instance.finished:
                        time = specific_instance.get_value("Time")
                        latex_plot_data += f"({average_discrete_states}, {time if time > min_value else min_value}) %{specific_instance.instance_name}\n"
                    else:
                        latex_plot_data += "" #Don't plot if not finish
                        # latex_plot_data += f"({average_discrete_states}, {did_not_finish_value}) %{specific_instance.instance_name}\n"
                latex_plot_data += "};\n"
        latex_legend_data += "}\n"
        output_latex_content(f"scaling_discrete_states_{alg}.txt", latex_legend_data + latex_plot_data)

def latex_cactus_plot(data: dict[str, list[InstanceResult]], category, output_name):
    data = prune_instances_not_on_all_algs(data, False)
    sort_results_data(data)

    instance_count = 0
    for (alg, instance_results) in data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        instance_count = len(instance_names)
        break

    latex_plot_data = "\legend{"
    for alg in data.keys():
        latex_plot_data += alg_to_table_name[alg] + ", "
    latex_plot_data += "}\n% Number of instances: " + str(instance_count) + "\n"

    min_value = 0.001
    for alg, instance_results in data.items():
        latex_plot_data += "\\addplot[mark=none, " + f"{alg_to_plot_options_dict[alg]}" + "] coordinates {\n"
        count = 0
        for instance_result in sorted(instance_results, key=lambda x: x.get_value(category)):
            if not instance_result.finished:
                continue
            val = instance_result.get_value(category)
            if val == -1:
                continue
            latex_plot_data += f"({count}, {val if val >= min_value else 0.001}) %{instance_result.instance_name} \n"
            count += 1
        latex_plot_data += "};\n"

    output_latex_content(f"{output_name}.txt", latex_plot_data)

def output_latex_content(file_name, content):
    print(f"Writing to file: 'latex/{file_name}'")
    latex_file_table = open(os.path.join(os.getcwd(), f"latex/{file_name}"), "w")
    latex_file_table.write(content)

def sort_results_data(results_data: dict[str, list[InstanceResult]]):
    for alg, instances in results_data.items():
        results_data[alg] = sorted(instances, key=lambda x: x.instance_name)

def prune_instances_not_on_all_algs(data: dict[str, list[InstanceResult]], also_prune_non_finished_instances: bool) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    common_instances_names = {}
    count = 0
    for alg, instances in data.items():
        if count == 0:
            if also_prune_non_finished_instances:
                common_instances_names = set([instance.instance_name for instance in instances if instance.finished])
            else:
                common_instances_names = set([instance.instance_name for instance in instances])
        else:
            if also_prune_non_finished_instances:
                new_instance_names = set([instance.instance_name for instance in instances if instance.finished])
            else:
                new_instance_names = set([instance.instance_name for instance in instances])
            common_instances_names = common_instances_names.intersection(new_instance_names)
        count += 1

    for alg, instances in data.items():
        remaining_instances = [instance for instance in instances if instance.instance_name in common_instances_names]
        if len(remaining_instances) > 0:
            result_data[alg] = remaining_instances
    return result_data

def prune_instances_containing_str(data: dict[str, list[InstanceResult]], str_list: list[str]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    for alg, instances in data.items():
        remaining_instances = [instance for instance in instances if len([s for s in str_list if s in instance.instance_name]) == 0]
        if len(remaining_instances) > 0:
            result_data[alg] = remaining_instances
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

def latex_big_table(data: dict[str, list[InstanceResult]], output_name, alg_order):
    alg_to_table_columns: {str: list[str]} = {
        "lambdadeduction": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_full_no_reuse_waiting": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_no_optimisations": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_reuse_waiting": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_prune_parent": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_transformation_matrix": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_full_reset_cost": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_keep_parent": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "concretemcr": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "concretemcr_por": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"]
    }
    column_to_table_name: {str: str} = {
        "TotalTime": "Time (s)",
        "Memory": "Memory (MB)",
        "LpsSolved": "LPs",
        "Iterations": "Iter",
        "BestRatio": "Ratio",
        "ReductionTime": "Reduc. (s)",
        "HowardTime": "Howard (s)",
        "PorTime": "Por (s)",
        "BestRatioTime": "RatioTime (s)"
    }

    data = prune_instances_not_on_all_algs(data, False)
    sort_results_data(data)
    new_data = OrderedDict((k, data.get(k)) for k in alg_order)

    latex_table = r"\begin{tabular}{c"
    for alg in data.keys():
        latex_table += "|"
        for column in alg_to_table_columns[alg]:
            latex_table += "r"
    latex_table += "}\n"

    for alg in new_data.keys():
        latex_table += "& \multicolumn{" + str(len(alg_to_table_columns[alg])) + "}{c}{" + alg_to_table_name[alg] + "} "
    latex_table += "\\\\\\hline\n"

    latex_table += "Instance"

    for alg in new_data.keys():
        for column in alg_to_table_columns[alg]:
            latex_table += " & " + column_to_table_name[column]
    latex_table += "\\\\\\hline"

    instance_names: list[str] = []
    for (alg, instance_results) in new_data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        break

    previous_instance_name = ""
    for instance_name in instance_names:
        if instance_name.split("_")[0] != previous_instance_name.split("_")[0]:
            latex_table += "\hline\n"
        instance_latex_table = ""
        previous_instance_name = instance_name
        instance_latex_table += instance_name.replace("_", "\_").replace("strandvejen", "strdvj")
        best_time_for_instance = 1000000
        best_memory_for_instance = 1000000
        best_ratio_for_instance = 1000000
        best_ratiotime_for_instance = 1000000

        for (alg, instance_results) in new_data.items():
            instance_result: InstanceResult = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
            for column in alg_to_table_columns[alg]:
                instance_latex_table += " & "
                match column:
                    case "TotalTime":
                        if instance_result.out_of_time:
                            instance_latex_table += "OOT"
                        elif instance_result.finished:
                            time_to_finish = (instance_result.time_to_finish / 1000)
                            if time_to_finish < best_time_for_instance:
                                instance_latex_table = instance_latex_table.replace("-besttime-", "")
                                instance_latex_table += "-besttime-"
                                best_time_for_instance = time_to_finish
                            elif time_to_finish == best_time_for_instance:
                                instance_latex_table += "-besttime-"
                            instance_latex_table += "%.3f" % time_to_finish
                        else:
                            instance_latex_table += "-"
                    case "Memory":
                        if instance_result.out_of_memory:
                            instance_latex_table += "OOM"
                        elif instance_result.finished:
                            memory = (instance_result.memory_script / 1000)
                            if memory < best_memory_for_instance:
                                instance_latex_table = instance_latex_table.replace("-bestmemory-", "")
                                instance_latex_table += "-bestmemory-"
                                best_memory_for_instance = memory
                            elif memory == best_memory_for_instance:
                                instance_latex_table += "-bestmemory-"
                            instance_latex_table += "%.3f" % memory
                        else:
                            instance_latex_table += "-"
                    case "LpsSolved":
                        instance_latex_table += f"{instance_result.total_lp_count}"
                    case "Iterations":
                        instance_latex_table += f"{len(instance_result.ratios) + 1}"
                    case "BestRatio":
                        if len(instance_result.ratios) > 0:
                            best_ratio = float("%.4f" % instance_result.ratios[-1][0])
                            if best_ratio < best_ratio_for_instance:
                                instance_latex_table = instance_latex_table.replace("-bestratio-", "")
                                instance_latex_table += "-bestratio-"
                                best_ratio_for_instance = float("%.4f" % best_ratio)
                            elif best_ratio == best_ratio_for_instance:
                                instance_latex_table += "-bestratio-"
                            instance_latex_table += "%.4f" % best_ratio
                        elif not instance_result.out_of_time and not instance_result.out_of_memory:
                            instance_latex_table += "\\textbf{No sol.}"
                            best_ratio_for_instance = -1
                        else:
                            instance_latex_table += "-"
                    case "BestRatioTime":
                        if len(instance_result.ratios) > 0:
                            best_ratio_time = instance_result.ratios[-1][1] / 1000
                            if best_ratio_time < best_ratiotime_for_instance:
                                instance_latex_table = instance_latex_table.replace("-bestratiotime-", "")
                                instance_latex_table += "-bestratiotime-"
                                best_ratiotime_for_instance = best_ratio_time
                            elif best_ratio_time == best_ratiotime_for_instance:
                                instance_latex_table += "-bestratiotime-"
                            instance_latex_table += "%.3f" % best_ratio_time
                        else:
                            instance_latex_table += "-"
                    case "ReductionTime":
                        if instance_result.mcr_reduction_time == -1:
                            instance_latex_table += "-"
                        else:
                            instance_latex_table += "%.3f" % (instance_result.mcr_reduction_time / 1000)
                    case "HowardTime":
                        if instance_result.howards_time == -1:
                            instance_latex_table += "-"
                        else:
                            instance_latex_table += "%.3f" % (instance_result.howards_time / 1000)
                    case "PorTime":
                        if instance_result.por_time == -1:
                            instance_latex_table += "-"
                        else:
                            instance_latex_table += "%.3f" % (instance_result.por_time / 1000)
        instance_latex_table += "\\\\\\hline\n"
        res = re.findall(r"-bestratio-(\d+.\d+)", instance_latex_table)
        for r in res:
            instance_latex_table = instance_latex_table.replace(f"-bestratio-{r}", "\\textbf{" + r + "}")
        res = re.findall(r"-besttime-(\d+.\d+)", instance_latex_table)
        for r in res:
            instance_latex_table = instance_latex_table.replace(f"-besttime-{r}", "\\textbf{" + r + "}")
        res = re.findall(r"-bestratiotime-(\d+.\d+)", instance_latex_table)
        for r in res:
            instance_latex_table = instance_latex_table.replace(f"-bestratiotime-{r}", "\\textbf{" + r + "}")
        res = re.findall(r"-bestmemory-(\d+.\d+)", instance_latex_table)
        for r in res:
            instance_latex_table = instance_latex_table.replace(f"-bestmemory-{r}", "\\textbf{" + r + "}")
        latex_table += instance_latex_table
    latex_table += "\\end{tabular}"
    output_latex_content(f"{output_name}.txt", latex_table)

def latex_scatter_plot(data: dict[str, list[InstanceResult]], x_alg_name, y_alg_name, category_name, output_name, did_not_finish_value):
    instance_type_to_mark_options = {
        "general": "mark=+, color=black",
        "strandvejen": "mark=square, color=red",
        "surveil": "mark=o, color=dgreen",
        "job": "mark=triangle, color=blue"
    }

    instance_type_to_points: dict[str, list[str]] = {}

    data = prune_instances_not_on_all_algs(data, False)
    sort_results_data(data)

    instance_names: list[str] = []
    for (alg, instance_results) in data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        break

    min_value = 0.001
    for instance_name in instance_names:
        x_alg_value = -1
        y_alg_value = -1
        for (alg, instance_results) in data.items():
            instance_result: InstanceResult = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
            if alg == x_alg_name:
                if not instance_result.finished:
                    x_alg_value = did_not_finish_value
                else:
                    val = instance_result.get_value(category_name)
                    x_alg_value = val if val >= min_value else min_value
            elif alg == y_alg_name:
                if not instance_result.finished:
                    y_alg_value = did_not_finish_value
                else:
                    val = instance_result.get_value(category_name)
                    y_alg_value = val if val >= min_value else min_value
            else:
                continue
        instance_type_name = instance_name.split("_")[0]
        if instance_type_name not in instance_type_to_points.keys():
            instance_type_to_points[instance_type_name] = []
        instance_type_to_points[instance_type_name].append(f"({x_alg_value}, {y_alg_value})")
        # latex_plot_data += f"({x_alg_value}, {y_alg_value}) "
    # latex_plot_data += "\n};"

    general_latex_plot_data = "\\addplot+[only marks, " + instance_type_to_mark_options["general"] + "] coordinates {\n"
    non_special_instance_found = False
    special_instances_plot_data = ""
    for instance_type_name, points in instance_type_to_points.items():
        if len(points) == 0:
            continue

        if instance_type_name in instance_type_to_mark_options.keys():
            instance_type_data = "\\addplot+[only marks, " + instance_type_to_mark_options[instance_type_name] + "] coordinates {\n"
            for point in points:
                instance_type_data += point + " "
            instance_type_data += "};\n"
            special_instances_plot_data += instance_type_data
        else:
            for point in points:
                general_latex_plot_data += point + " "
            non_special_instance_found = True
    general_latex_plot_data += "\n};\n"

    latex_plot_data = special_instances_plot_data + (general_latex_plot_data if non_special_instance_found else "")
    output_latex_content(f"{output_name}.txt", latex_plot_data)

def filter_to_specific_algs(data: dict[str, list[InstanceResult]], algs: list[str]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}
    for alg, instances in data.items():
        if alg in algs:
            result_data[alg] = instances
    return result_data

def calc_median_values(data: dict[str, list[InstanceResult]], alg1: str, alg2: str, category: str, output_name: str):
    data = prune_instances_not_on_all_algs(data, False)
    sort_results_data(data)

    instance_names: list[str] = []
    for (alg, instance_results) in data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        break

    points = []
    for instance_name in instance_names:
        alg1_val = -1
        alg2_val = -1
        for (alg, instance_results) in data.items():
            instance_result: InstanceResult = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
            if alg == alg1:
                val = instance_result.get_value(category)
                if instance_result.finished:
                    alg1_val = val
            elif alg == alg2:
                val = instance_result.get_value(category)
                if instance_result.finished:
                    alg2_val = val
            else:
                continue
        if alg1_val == -1 and alg2_val == -1:
            continue
        elif alg1_val == -1:
            points.append(-10000)
        elif alg2_val == -1:
            points.append(10000)
        else:
            if alg1_val == 0:
                alg1_val = 0.001
            if alg2_val == 0:
                alg2_val = 0.001
            points.append(float(alg2_val - alg1_val)/alg1_val)
    points.sort()
    lowest_val = points[0]
    highest_val = points[-1]
    median_index = int(len(points) / 2)
    median_val = points[median_index]

    output_str = f"{alg1} - {alg2} - {category}\nMedian: {median_val}\nLowest: {lowest_val}\nHighest: {highest_val}"

    output_latex_content(f"{output_name}.txt", output_str)



os.chdir("../results")
result_data = parse_result_data(os.getcwd(), 1800, 10000)

os.chdir("../")
latex_dir = os.path.join(os.getcwd(), f"latex")
if not os.path.exists(latex_dir) or not os.path.isdir(latex_dir):
    os.mkdir(latex_dir)

# result_data = filter_instances_to_contain_str(result_data, "-")
# result_data = filter_instances_to_contain_str(result_data, "scaling")
result_data = prune_instances_containing_str(result_data, ["scaling"])
# result_data = prune_instances_containing_str(result_data, ["a2_p5", "a2_p6", "a2_p7", "a3_p4", "a3_p5", "a3_p6", "a3_p7"])
# result_data = prune_instances_not_on_all_algs(result_data, True)

# result_data = filter_to_specific_algs(result_data, ["lambdadeduction", "lambdadeduction_no_optimisations", "lambdadeduction_reuse_waiting", "lambdadeduction_prune_parent", "lambdadeduction_transformation_matrix"])
# latex_cactus_plot(result_data, "Memory", "cactus_memory_lambda_data")
# latex_cactus_plot(result_data, "Time", "cactus_time_lambda_data")
# latex_big_table(result_data, "test_table_data", ["lambdadeduction", "lambdadeduction_no_optimisations", "lambdadeduction_reuse_waiting", "lambdadeduction_prune_parent", "lambdadeduction_transformation_matrix"])
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_prune_parent", "Memory", "prune_parent_median_memory")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_prune_parent", "Time", "prune_parent_median_time")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_transformation_matrix", "Memory", "transformation_matrix_median_memory")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_transformation_matrix", "Time", "transformation_matrix_median_time")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_reuse_waiting", "Memory", "reuse_waiting_median_memory")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction_reuse_waiting", "Time", "reuse_waiting_median_time")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction", "Memory", "lambdadeduction_median_memory")
# calc_median_values(result_data, "lambdadeduction_no_optimisations", "lambdadeduction", "Time", "lambdadeduction_median_time")

# result_data = filter_to_specific_algs(result_data, ["lambdadeduction", "lambdadeduction_full_no_reuse_waiting", "lambdadeduction_reuse_waiting", "lambdadeduction_prune_parent", "lambdadeduction_transformation_matrix", "lambdadeduction_no_optimisations", "concretemcr"])
# latex_big_table(result_data, "test_table_data", ["lambdadeduction", "lambdadeduction_full_no_reuse_waiting", "lambdadeduction_reuse_waiting", "lambdadeduction_prune_parent", "lambdadeduction_transformation_matrix", "lambdadeduction_no_optimisations", "concretemcr"])

# result_data = filter_to_specific_algs(result_data, ["lambdadeduction", "lambdadeduction_no_optimisations"])
# latex_big_table(result_data, "big_table_lambda_data", ["lambdadeduction", "lambdadeduction_no_optimisations"])

result_data = filter_to_specific_algs(result_data, ["lambdadeduction_full_no_reuse_waiting", "concretemcr"])
# latex_cactus_plot(result_data, "Time", "cactus_time_data")
# latex_cactus_plot(result_data, "Memory", "cactus_memory_data")
calc_median_values(result_data, "lambdadeduction_full_no_reuse_waiting", "concretemcr", "Memory", "concretemcr_median_memory")
calc_median_values(result_data, "lambdadeduction_full_no_reuse_waiting", "concretemcr", "Time", "concretemcr_median_time")
# latex_scatter_plot(result_data, "lambdadeduction_full_no_reuse_waiting", "concretemcr", "Time", "scatter_plot_time_data", 5000)
# latex_scatter_plot(result_data, "lambdadeduction_full_no_reuse_waiting", "concretemcr", "Memory", "scatter_plot_memory_data", 50000)
# latex_big_table(result_data, "big_table_data", ["concretemcr", "lambdadeduction_full_no_reuse_waiting"])

# result_data = filter_to_specific_algs(result_data, ["lambdadeduction_full_no_reuse_waiting"])
# result_data = prune_instances_containing_str(result_data, ["scaling"])
# result_data = filter_instances_to_contain_str(result_data, "strandvejen")
# latex_ratio_step_plots_all_instances(result_data, "lambdadeduction_full_no_reuse_waiting")

# latex_state_scaling_plot(result_data)
# result_data = filter_to_specific_algs(result_data, ["lambdadeduction_full_no_reuse_waiting"])
# latex_constant_scaling_plot(result_data, "lambdadeduction_constant_scaling_plus1_plot_data", "lambdadeduction_full_no_reuse_waiting")

#latex_ratio_step_plots_all_instances(result_data)
