package library_ops.github_actions

deny contains msg if {
  not input.permissions
  msg := sprintf("Workflow %s must declare top-level permissions.", [object.get(input, "name", "<unknown>")])
}

deny contains msg if {
  some job_name
  job := input.jobs[job_name]
  job["runs-on"] == "self-hosted"
  msg := sprintf("Workflow %s job %s uses self-hosted runner without an ADR.", [object.get(input, "name", "<unknown>"), job_name])
}

deny contains msg if {
  some job_name, step_index
  step := input.jobs[job_name].steps[step_index]
  contains(step.run, "curl ")
  contains(step.run, "| sh")
  msg := sprintf("Workflow %s job %s step %d pipes curl to shell.", [object.get(input, "name", "<unknown>"), job_name, step_index])
}
