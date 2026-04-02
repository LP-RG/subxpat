module madd_i126_o84 (a, b, c, r);
input [41:0] a,b,c;
output [83:0] r;

assign r = (a * b) + c;

endmodule
