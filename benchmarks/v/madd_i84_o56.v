module madd_i84_o56 (a, b, c, r);
input [27:0] a,b,c;
output [55:0] r;

assign r = (a * b) + c;

endmodule
