module abs_diff_i328_o164(a,b,r);
input [163:0] a,b;
output [163:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
