module madd_i27_o18 (a, b, c, r);
input [8:0] a, b, c;
output [17:0] r;


assign r = (a * b) + c;

endmodule  
