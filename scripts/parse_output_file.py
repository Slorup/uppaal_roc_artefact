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
    "concretemcr": "color=red, loosely dashed, thick",
    "concretemcr_por": "color=green, thick",
    "lambdadeduction": "color=blue, dashed, thick",
    "lambdadeduction_lp": "color=purple, thick",
    "lambdadeduction_clean_waiting": "color=green, dotted"
}

alg_to_table_name: {str: str} = {
    "lambdadeduction": "Symbolic $\lambda$\\nobreakdash-deduction",
    "lambdadeduction_lp": "Symbolic $\lambda$\\nobreakdash-deduction without transformation matrices",
    "lambdadeduction_clean_waiting": "Symbolic $\lambda$\\nobreakdash-deduction with waiting list cleanup",
    "concretemcr": "Concrete-MCR",
    "concretemcr_por": "Concrete-MCR + POR"
}

class InstanceResult:
    def __init__(self, instance_name, ratios, time_to_find_optimal, time_to_finish, scaling_factor, finished, out_of_memory, out_of_time, uses_cost_reward, mcr_states, howards_time, por_time, mcr_reduction_time, total_lp_count, memory, clean_waiting, no_transformation_matrix):
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
        self.clean_waiting = clean_waiting
        self.no_transformation_matrix = no_transformation_matrix

    def get_value(self, category_str):
        match category_str:
            case "Time":
                return self.time_to_finish / 1000 if self.time_to_finish != -1 else -1
            case "Memory":
                return self.memory / 1000 if self.memory != -1 else -1

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

                    res = re.match("Timed Out", line)
                    if res:
                        out_of_time = True

                    res = re.match("Ratio type: Cost/Time", line)
                    if res:
                        uses_cost_reward = False

                    res = re.match(r"Number of states: (\d+)", line)
                    if res:
                        mcr_states = res.group(1)

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

                    res = re.match(r"@@@\d+.?\d+,(\d+)@@@", line)
                    if res:
                        memory = res.group(1)

                res = re.match(".*scaling(\d+)", instance)
                scaling_factor = -1
                if res:
                    scaling_factor = res.group(1)
                finished = not out_of_time and not out_of_memory
                res = InstanceResult(instance_name, ratios, int(optimal_ratio_time), int(total_time), int(scaling_factor), finished, out_of_memory, out_of_time, uses_cost_reward, int(mcr_states), int(howards_time), int(por_time), int(mcr_reduction_time), int(lp_total_count), int(memory), clean_waiting_list, no_transformation_matrix)
                result_dict[alg_name].append(res)
        alg_progress += 1
    return result_dict


def latex_ratio_step_plots_all_instances(data: dict[str, list[InstanceResult]]):
    alg, instance_results = list(data.items())[0]
    for instance in instance_results:
        latex_ratio_step_plot(data, instance.instance_name)

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

def latex_constant_scaling_plot(data: dict[str, list[InstanceResult]], output_name):
    latex_plot_legend = r"\legend{"
    for alg in data.keys():
        latex_plot_legend += f"{alg}, "
    latex_plot_legend +="}\n"

    latex_plot_data = ""
    for (alg, instance_results) in data.items():
        latex_plot_data += r"\addplot[mark=*, mark options={solid}, " +  f"{alg_to_plot_options_dict[alg]}] coordinates" + "{\n"
        #Finds all instances that contains 'instance_name' in their name and has a scaling factor
        scaling_instances = [instance_result for instance_result in instance_results if instance_result.scaling_factor != -1]
        scaling_instances = sorted(scaling_instances, key=lambda x: x.scaling_factor)
        for scaling_instance in scaling_instances:
            #Still includes instances where they did not finish (time_to_finish = -1)
            latex_plot_data += f"({scaling_instance.scaling_factor}, {scaling_instance.time_to_finish})\n"
        latex_plot_data += r"};" + "\n"
    output_latex_content(f"{output_name}.txt", latex_plot_legend + latex_plot_data)

def latex_cactus_plot(data: dict[str, list[InstanceResult]], category, output_name):
    data = prune_instances_not_on_all_algs(data)
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

    did_not_finish_replacement_val = 1000
    min_value = 0.001
    for alg, instance_results in data.items():
        latex_plot_data += "\\addplot[mark=none, " + f"{alg_to_plot_options_dict[alg]}" + "] coordinates {\n"
        count = 0
        for instance_result in sorted(instance_results, key=lambda x: x.get_value(category)):
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

def prune_instances_not_on_all_algs(data: dict[str, list[InstanceResult]]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}

    common_instances_names = {}
    count = 0
    for alg, instances in data.items():
        if count == 0:
            common_instances_names = set([instance.instance_name for instance in instances])
        else:
            new_instance_names = set([instance.instance_name for instance in instances])
            common_instances_names = common_instances_names.intersection(new_instance_names)
        count += 1

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

def latex_big_table(data: dict[str, list[InstanceResult]], output_name):
    alg_to_table_columns: {str: list[str]} = {
        "lambdadeduction": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_lp": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
        "lambdadeduction_clean_waiting": ["TotalTime", "Memory", "BestRatio", "BestRatioTime"],
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

    data = prune_instances_not_on_all_algs(data)
    sort_results_data(data)

    latex_table = r"\begin{tabular}{c"
    for alg in data.keys():
        latex_table += "|"
        for column in alg_to_table_columns[alg]:
            latex_table += "r"
    latex_table += "}\n"

    for alg in data.keys():
        latex_table += "& \multicolumn{" + str(len(alg_to_table_columns[alg])) + "}{c}{" + alg_to_table_name[alg] + "} "
    latex_table += "\\\\\\hline\n"

    latex_table += "Instance"

    for alg in data.keys():
        for column in alg_to_table_columns[alg]:
            latex_table += " & " + column_to_table_name[column]
    latex_table += "\\\\\\hline"

    instance_names: list[str] = []
    for (alg, instance_results) in data.items():
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

        for (alg, instance_results) in data.items():
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
                            memory = (instance_result.memory / 1000)
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

def latex_scatter_plot(data: dict[str, list[InstanceResult]], x_alg_name, y_alg_name, category_name, output_name):
    data = prune_instances_not_on_all_algs(data)
    sort_results_data(data)

    instance_names: list[str] = []
    for (alg, instance_results) in data.items():
        instance_names = [instance_result.instance_name for instance_result in instance_results]
        break

    latex_plot_data = "\\addplot+[only marks, mark=+, color=black] coordinates {\n"

    did_not_finish_value = 1000
    min_value = 0.001
    for instance_name in instance_names:
        x_alg_value = -1
        y_alg_value = -1
        for (alg, instance_results) in data.items():
            instance_result: InstanceResult = [instance_result for instance_result in instance_results if instance_result.instance_name == instance_name][0]
            if alg == x_alg_name:
                val = instance_result.get_value(category_name)
                if val == -1:
                    x_alg_value = did_not_finish_value
                else:
                    x_alg_value = val if val >= min_value else min_value
            elif alg == y_alg_name:
                val = instance_result.get_value(category_name)
                if val == -1:
                    y_alg_value = did_not_finish_value
                else:
                    y_alg_value = val if val >= min_value else min_value
            else:
                continue
        latex_plot_data += f"({x_alg_value}, {y_alg_value}) "
    latex_plot_data += "\n};"
    output_latex_content(f"{output_name}.txt", latex_plot_data)

def filter_to_specific_algs(data: dict[str, list[InstanceResult]], algs: list[str]) -> dict[str, list[InstanceResult]]:
    result_data: dict[str, list[InstanceResult]] = {}
    for alg, instances in data.items():
        if alg in algs:
            result_data[alg] = instances
    return result_data

os.chdir("../results")
result_data = parse_result_data(os.getcwd())
# result_data = prune_instances_containing_str(result_data, "plus1")
# result_data = filter_instances_to_contain_str(result_data, "surveil")
result_data = prune_instances_containing_str(result_data, "scaling")
result_data = filter_to_specific_algs(result_data, ["lambdadeduction", "lambdadeduction_lp"])
# result_data = prune_instances_not_on_all_algs(result_data)

os.chdir("../")
latex_dir = os.path.join(os.getcwd(), f"latex")
if not os.path.exists(latex_dir) or not os.path.isdir(latex_dir):
    os.mkdir(latex_dir)

# latex_cactus_plot(result_data, "Time", "cactus_time_data")
# latex_scatter_plot(result_data, "lambdadeduction", "lambdadeduction_lp", "Time", "scatter_plot_time_data")
# latex_big_table(result_data, "big_table_data")
# latex_data_structure_size_plot(os.getcwd() + "/results/lambdadeduction/strandvejen_test_f2_v1_c1.txt")
# latex_constant_scaling_plot(result_data, "constant_scaling_plus1_plot_data")
#latex_ratio_step_plots_all_instances(result_data)
