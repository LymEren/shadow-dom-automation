
# --------------------------- JavaScript Methods ---------------------------

def isElementVisible(self, jsPath):
    jsMethodBaseCode = """
    function isElementVisible(jsPath) {
        try {
            const element = eval(jsPath);
            if (!element) return false;

            const style = window.getComputedStyle(element);
            return style.visibility !== 'hidden' && 
                    style.display !== 'none' && 
                    element.offsetWidth > 0 && 
                    element.offsetHeight > 0;
        } catch (error) {
            console.error('Error evaluating element visibility:', error);
            return false;
        }
    }
    """
    jsExecCode = f"""
    return isElementVisible("{str(jsPath)}");
    """

    visibleStatus = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode)

    if visibleStatus:
        self.testCase.action.scrollToElement((jsPath, "jsPath"))
        self.testCase.action.highlight((jsPath, "jsPath"))
        return True
    else:
        raise Exception(f"This item is not visible on the page || JsPath: {str(jsPath)} ||")

def isElementClickable(self, jsPath):
    self.isElementVisible(jsPath)  # Check element visibility

    jsMethodBaseCode = """
    function isElementClickable(jsPath) {
        try {
            const element = eval(jsPath);
            if (!element) return false;
            
            if (element.disabled) return false;  // Check if element is disabled
            
            const style = window.getComputedStyle(element);  // Check if element has pointer-events set to none
            if (style.pointerEvents === 'none') return false;
            
            const rect = element.getBoundingClientRect();  // Check if element is within viewport
            if (rect.bottom < 0 || rect.top > window.innerHeight || 
                rect.right < 0 || rect.left > window.innerWidth) {
                return false;
            }
            
            const centerX = rect.left + rect.width / 2;  // Check if element is obscured by other elements
            const centerY = rect.top + rect.height / 2;
            const elementAtPoint = document.elementFromPoint(centerX, centerY);
            if (!element.contains(elementAtPoint) && !elementAtPoint.contains(element)) {
                return false;
            }
            
            return true;
        } catch (error) {
            console.error('Error evaluating element clickability:', error);
            return false;
        }
    }
    """

    jsExecCode = f"""
    return isElementClickable("{str(jsPath)}");
    """
    clickableStatus = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode)

    if clickableStatus:
        return True
    else:
        raise Exception(f"This item is not clickable || JsPath: {str(jsPath)} ||")

def getParentJsPath(self, jsPath, parentElementCount=1):
    jsMethodBaseCode = """
    function getParentJsPath(jsPath, parentElementCount=1) {
        try {
            let element = eval(jsPath); // Evaluate the original path to get the element
            let path = jsPath;

            for (let i = 0; i < parentElementCount; i++) {
                element = element.parentElement;
                path += '.parentElement';

                if (!element) {
                    console.error("Reached top-level element, cannot go up further");
                    return null;
                }
            }

            return path;
        } catch (error) {
            console.error("Error getting parent:", error);
            return null;
        }
    }
    """

    jsExecCode = f"""
    return getParentJsPath("{str(jsPath)}", {str(parentElementCount)});
    """

    self.testCase.log(
        f"Js method getParentJsPath executing. JsPath: {str(jsPath)}, parentElementCount: {str(parentElementCount)}")
    jsPath = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode, returnResponseMessage=True)

    if jsPath is None:
        raise Exception(f"Element can not found.")
    else:
        return jsPath

def waitForElement_jsMethod(self, jsPath=None, waitTime=20, desiredText=None, parentTag=None, exactValue=False):
    """
    Wait for an element to be visible on the page.

    Args:
        jsPath: JavaScript path to the element (optional if desiredText and parentTag are provided)
        waitTime: Maximum time to wait in seconds (default: 20)
        desiredText: Text to search for (optional, requires parentTag)
        parentTag: Parent tag to search within (optional, requires desiredText)
        exactValue: Whether to match the text exactly or allow partial matches (default: False)

    Returns:
        JavaScript path to the found element

    Raises:
        Exception: If element is not found or not visible after waitTime
    """

    if jsPath is None and (desiredText is None or parentTag is None):  # Check Parameters
        self.testCase.log("Either jsPath or both desiredText and parentTag must be provided")

    if desiredText and parentTag:  # You can use this function with text
        jsPath = self.getJsPathWithText(desiredText, parentTag, exactValue=exactValue)

    self.testCase.log(f"Js method waitForElement_jsMethod executing. || Wait time: {str(waitTime)} || JsPath: {str(jsPath)} ||")

    loopFailFlag = True
    for i in range(int(waitTime)):  # Wait for element retry mechanism
        try:
            visibleStatus = self.isElementVisible(jsPath)
            if visibleStatus is True:
                self.testCase.log(f"This element became visible and found on the page || JsPath: {str(jsPath)} ||")

                self.testCase.action.scrollToElement((jsPath, "jsPath"))
                self.testCase.action.highlight((jsPath, "jsPath"))
                loopFailFlag = False
                break
            else:
                self.testCase.log(f"This item was not visible on the page || Wait time: {i + 1}/{waitTime} || JsPath: {str(jsPath)} ||")
                self.testCase.sleep(1, addToConsole=False)
                try:
                    self.testCase.log(f"This item was not visible on the page|| Wait time: {i} || JsPath: {str(jsPath)} ||")
                    self.testCase.action.scrollToElement((jsPath, "jsPath"))
                except:
                    pass
        except:
            self.testCase.sleep(1, addToConsole=False)

    if loopFailFlag:
        # If the loop completes without breaking, raise an exception
        raise Exception(f"This item was not visible on the page || JsPath: {str(jsPath)} ||")

    return jsPath

def getJsPathWithText(self, desiredText, parentTag, getParentPath=False, exactValue=False, waitTime=3):
    jsMethodBaseCode = """
    function getJsPathWithText(desiredText, parentTag, getParentPath = false, exactValue = false) {
        function searchInNode(node, path) {
            // Check if the node contains the desired text
            if (node.textContent) {
                let isMatch = false;
                
                if (exactValue) {
                    // Exact match with trim
                    isMatch = node.textContent.trim() === desiredText;
                } else {
                    // Partial match (includes)
                    isMatch = node.textContent.includes(desiredText);
                }
                
                if (isMatch) {
                    return path;
                }
            }
            
            // If the node has a shadow root, continue searching recursively
            if (node.shadowRoot) {
                const shadowChildren = node.shadowRoot.querySelectorAll('*');
                for (let childIndex = 0; childIndex < shadowChildren.length; childIndex++) {
                    const shadowChild = shadowChildren[childIndex];
                    
                    let childPath;
                    if (getParentPath) {
                        childPath = path;
                    } else {
                        childPath = `${path}.shadowRoot.querySelectorAll('*')[${childIndex}]`;
                    }
                    
                    const result = searchInNode(shadowChild, childPath);
                    if (result) return result;
                }
            }
            return null;
        }
    
        const shadowParents = document.querySelectorAll(parentTag);
        for (let parentIndex = 0; parentIndex < shadowParents.length; parentIndex++) {
            const exactParent = shadowParents[parentIndex];
            
            let parentPath;
            parentPath = `document.querySelectorAll('${parentTag}')[${parentIndex}]`;
            
            const result = searchInNode(exactParent, parentPath);
            if (result) return result;
        }
        console.log('Element with text not found:', desiredText);
        return null;
    }
    """

    jsExecCode = f"""
    return getJsPathWithText('{str(desiredText)}', '{str(parentTag)}', {str(getParentPath).lower()}, {str(exactValue).lower()});
    """

    self.testCase.log(f"Js method getJsPathWithText executing, {str(desiredText)} trying to found under {str(parentTag)}.")
    jsPath = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode, returnResponseMessage=True)

    self.waitForElement_jsMethod(jsPath, waitTime=waitTime)

    if jsPath is None:
        raise Exception(f"Element with text {str(desiredText)} not found under {str(parentTag)}")
    else:
        return jsPath

def clickElementUnderShadowRoot(self, baseJsPath, selector="*", waitTime=5):
    jsMethodBaseCode = """
    function clickElementUnderShadowRoot(jsPath, selector = '*') {
        let element;
        element = eval(jsPath);

        if (!element || !element.shadowRoot) {
            console.log('Element or shadowRoot not found for path:', jsPath);
            return false;
        }
        const clickableElement = element.shadowRoot.querySelector(selector);
        if (clickableElement) {
            return `${jsPath}.shadowRoot.querySelector("${selector}")`;
        } else {
            console.log('No child element to click in shadowRoot for path:', jsPath);
            return false;
        }
    }
    """

    self.testCase.log(
        f"Js method clickElementUnderShadowRoot executing, system trying to click element under {str(baseJsPath)}")

    jsExecCode = f"""
    return clickElementUnderShadowRoot("{str(baseJsPath)}", "{str(selector)}");
    """

    jsPath = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode, returnResponseMessage=True)

    # loopFailFlag = True
    # for i in range(int(waitTime)):  # Wait for element retry mechanism
    #     try:
    #         clickableStatus = self.isElementClickable(jsPath)
    #         if clickableStatus is True:
    #             loopFailFlag = False
    #             break
    #         else:
    #             self.testCase.sleep(1, addToConsole=False)
    #             self.testCase.log(f"This item was not clickable on the page || Wait time: {i + 1}/{waitTime} || JsPath: {str(jsPath)} ||")
    #     except:
    #         self.testCase.log(f"This item was not clickable on the page|| Wait time: {i} || JsPath: {str(jsPath)} ||")
    #         self.testCase.sleep(1, addToConsole=False)
    #
    # if loopFailFlag:
    #     # If the loop completes without breaking, raise an exception
    #     raise Exception(f"This item was not clickable on the page || JsPath: {str(jsPath)} ||")

    self.testCase.action.execJS(jsPath + ".click()")

def getElementJsPathWithTextAndSpecificParent(self, desiredText, parentJsPath, parentElementCount=1):
    jsMethodBaseCode = """
    function getElementJsPathWithTextAndSpecificParent(desiredText, parentJsPath, parentElementCount = 1) {
        let path = parentJsPath;
        let element;
        try {
            element = eval(path);
        } catch (e) {
            console.log('Invalid parentJsPath:', path);
            return '';
        }

        for (let i = 0; i < parentElementCount; i++) {
            element = element.parentElement;
            path += '.parentElement';
        }

        const elementsStack = [{el: element, elPath: path}];
        let foundPath = '';

        while (elementsStack.length > 0) {
            const {el: currentElement, elPath: currentPath} = elementsStack.pop();

            if (currentElement.textContent.includes(desiredText)) {
                foundPath = currentPath;
            }

            if (currentElement.shadowRoot && currentElement.shadowRoot.textContent.includes(desiredText)) {
                let children = Array.from(currentElement.shadowRoot.querySelectorAll('*'));
                for (let i = 0; i < children.length; i++) {
                    elementsStack.push({
                        el: children[i],
                        elPath: `${currentPath}.shadowRoot.querySelectorAll('*')[${i}]`
                    });
                }
            }

            let children = Array.from(currentElement.querySelectorAll('*'));
            for (let i = 0; i < children.length; i++) {
                elementsStack.push({
                    el: children[i],
                    elPath: `${currentPath}.querySelectorAll('*')[${i}]`
                });
            }
        }
        return foundPath;
    }
    """

    jsExecCode = f"""
    return getElementJsPathWithTextAndSpecificParent("{str(desiredText)}", "{str(parentJsPath)}", {str(parentElementCount)});
    """

    self.testCase.log(
        f"Js method getElementJsPathWithTextAndSpecificParent executing, {str(desiredText)} trying to found under {str(parentJsPath)}")

    jsPath = self.testCase.action.execJS(jsMethodBaseCode + jsExecCode, returnResponseMessage=True)

    self.testCase.action.scrollToElement((jsPath, "jsPath"))
    self.testCase.action.highlight((jsPath, "jsPath"))

    if jsPath is None:
        raise Exception(f"Element with text {str(desiredText)} not found under {str(parentJsPath)}")
    else:
        return jsPath
