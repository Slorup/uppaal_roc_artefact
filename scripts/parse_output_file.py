import os.path
import re
import datetime

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
    "concretemcr": "mark=*, mark options={solid}, color=red, loosely dashed, thick",
    "concretemcr_por": "mark=*, mark options={solid}, color=green, thick",
    "lambdadeduction": "mark=*, mark options={solid}, color=blue, dashed, thick"
}

def parse_result_data(result_folder):
    result_dict: dict[str, list[InstanceResult]] = {}
    alg_progress = 1
    ns_to_s_divider = 1000000000
    for alg_name in os.listdir(result_folder):
        print(f"Parsing results for algorithm {alg_name} - {alg_progress}/{len(os.listdir(result_folder))}")
        result_dict[alg_name] = []
        for instance in os.listdir(f"{result_folder}/{alg_name}"):
            with open(f"{result_folder}/{alg_name}/{instance}", "r") as file:
                lines = file.readlines()
                start_time = -1
                stop_time = -1
                ratios = []
                instance_name = instance.split('.')[0]
                if instance_name in instance_to_ratio_dict:
                    optimal_ratio = instance_to_ratio_dict[instance_name]
                else:
                    optimal_ratio = None
                optimal_ratio_time = -1
                for line in lines:
                    res = re.match("Start time: (\d+)", line)
                    if res:
                        start_time = round(float(res.group(1)))/ns_to_s_divider

                    res = re.match(r"Found new better ratio: (\d*\.?\d+(?:[e][-+]\d+)?) \(Time: (\d+)\)", line)
                    if res:
                        ratio = float(res.group(1))
                        time = round(float(res.group(2)))/ns_to_s_divider - start_time
                        if optimal_ratio is not None and abs(ratio - optimal_ratio) <= 0.0000001:
                            optimal_ratio_time = time
                        ratios.append((ratio, time))

                    res = re.match("Stop time: (\d+)", line)
                    if res:
                        stop_time = round(float(res.group(1)))/ns_to_s_divider
                total_time = stop_time - start_time
                res = re.match(".*scaling(\d+)", instance)
                scaling_factor = -1
                if res:
                    scaling_factor = res.group(1)
                res = InstanceResult(instance_name, ratios, optimal_ratio_time, total_time, scaling_factor)
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
        for ratio, time in instance_result.ratios:
            latex_plot_data += f"({time}, {ratio})\n"
        latex_plot_data += f"({instance_result.time_to_finish}, {instance_result.ratios[-1][0]}) %Finish time\n"
        latex_plot_data += r"};" + "\n"

    output_latex_content(f"{instance_name}_plot_data.txt", latex_plot_legend + latex_plot_data)

def latex_constant_scaling_plot(data):
    latex_plot_legend = r"\legend{"
    for alg in data.keys():
        latex_plot_legend += f"{alg}, "
    latex_plot_legend +="}\n"

    latex_plot_data = ""
    for (alg, instace_results) in data.items():
        latex_plot_data += r"\addplot" + f"[{alg_to_plot_options_dict[alg]}] coordinates" + "{\n"
        scaling_instances = [instance_result for instance_result in instace_results if instance_result.scaling_factor != -1] #TODO: use other 'non-exist' value
        for scaling_instance in scaling_instances:
            latex_plot_data += f"({scaling_instance.scaling_factor}, {scaling_instance.time_to_finish})\n"
        latex_plot_data += r"};" + "\n"
    output_latex_content(f"constant_scaling_plot_data.txt", latex_plot_legend + latex_plot_data)

def output_latex_content(file_name, content):
    print(f"Writing to file: 'latex/{file_name}'")
    latex_file_table = open(os.path.join(os.getcwd(), f"latex/{file_name}"), "w")
    latex_file_table.write(content)


class InstanceResult:
    def __init__(self, instance_name, ratios, time_to_find_optimal, time_to_finish, scaling_factor):
        self.instance_name = instance_name
        self.ratios = ratios
        self.time_to_find_optimal = time_to_find_optimal
        self.time_to_finish = time_to_finish
        self.scaling_factor = scaling_factor


def sort_results_data(results_data: dict[str, list[InstanceResult]]):
    for alg, instances in results_data.items():
        results_data[alg] = sorted(instances, key=lambda x: x.instance_name)

def prune_instances_not_on_all_algs(result_data: dict[str, list[InstanceResult]]):
    common_instances = {}
    count = 0
    for alg, instances in result_data.items():
        if count == 0:
            common_instances = set(instances)
        else:
            common_instances.intersection(set(instances))
        count += 1

    common_instances_names = set(map(lambda x: x.instance_name, common_instances))

    for alg, instances in result_data.items():
        remaining_instances = [instance for instance in instances if instance.instance_name in common_instances_names]
        result_data[alg] = remaining_instances

    sort_results_data(result_data)


os.chdir("../results")
result_data = parse_result_data(os.getcwd())
prune_instances_not_on_all_algs(result_data)

os.chdir("../")
latex_dir = os.path.join(os.getcwd(), f"latex")
if not os.path.exists(latex_dir) or not os.path.isdir(latex_dir):
    os.mkdir(latex_dir)

latex_constant_scaling_plot(result_data)
#latex_ratio_step_plots_all_instances(result_data)
