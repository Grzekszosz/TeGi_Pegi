# build_graph_from_cvs.py
from cv_reader.graph_builder import CVGraphBuilder


def main():
    builder = CVGraphBuilder()

    # jeśli chcesz za każdym razem mieć czystą bazę:
    builder.reset_graph()

    builder.process_all_cvs()


if __name__ == "__main__":
    main()
