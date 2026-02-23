module madd_i258_o172 (a, b, c, r);
input [85:0] a,b,c;
output [171:0] r;

assign r = (a * b) + c;

endmodule
