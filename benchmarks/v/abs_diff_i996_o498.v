module abs_diff_i996_o498(a,b,r);
input [497:0] a,b;
output [497:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
