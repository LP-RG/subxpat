module madd_i237_o158 (a, b, c, r);
input [78:0] a,b,c;
output [157:0] r;

assign r = (a * b) + c;

endmodule
