# Ruleset Descriptions

This folder contains various rulesets for validating Postman collections and workspaces using Spectral.

## Available Rulesets

### [rules.yaml](rules.yaml)
The default ruleset for validating Postman collections. Includes rules for:
- Collection structure validation
- Request/response validation
- Authentication checks
- URL and parameter validation 
- Naming conventions

### [workspacerules.yaml](workspacerules.yaml) 
Rules specific to Postman workspace validation:
- Workspace description requirements
- Collection naming and content rules
- Environment naming conventions
- Mock and monitor status checks
- API versioning rules

### [publicworkspacerules.yaml](publicworkspacerules.yaml)
Similar to workspacerules.yaml but specifically tuned for public workspaces. Available in both YAML and JSON formats.

### [goldenworkspacerules.yaml](goldenworkspacerules.yaml)
Enhanced ruleset with additional quality checks for "golden" or reference workspaces:
- Detailed collection documentation rules
- Security best practices
- Testing requirements
- URL and endpoint conventions
- Folder organization rules

## Usage

These rulesets can be used with the linter script by specifying the ruleset path:

```sh
python linter.py -c <collectionId> -r rulesets/rules.yaml
