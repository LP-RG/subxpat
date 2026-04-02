module madd_i66_o44 (a, b, c, r);
input [21:0] a,b,c;
output [43:0] r;

assign r = (a * b) + c;

endmodule
