module madd_i57_o38 (a, b, c, r);
input [18:0] a,b,c;
output [37:0] r;

assign r = (a * b) + c;

endmodule
