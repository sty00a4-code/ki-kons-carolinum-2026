// require.resolve findet die Regeln auch in der Umgebung von pre-commit (NODE_PATH).
module.exports = {
  extends: [require.resolve("stylelint-config-standard")],
};
