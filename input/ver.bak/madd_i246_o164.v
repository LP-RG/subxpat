module madd_i246_o164 (a, b, c, r);
input [81:0] a,b,c;
output [163:0] r;

assign r = (a * b) + c;

endmodule
