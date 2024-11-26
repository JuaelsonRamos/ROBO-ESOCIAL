from __future__ import annotations


def main():
    from src.gui.app import App

    root = App()

    # Precisa ser importado depois da inicialização da janela
    import src.gui.styles as style

    style.default()

    from src.gui.asyncio import Thread

    root.mainloop()
    Thread.stop_all()


if __name__ == '__main__':
    main()
